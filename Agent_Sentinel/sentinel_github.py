#!/usr/bin/env python3
"""
🤖 AmazingCoolFinds — Pipeline Maintenance Agent v2.0
======================================================
Autonomous agent that runs after every pipeline execution to:
1. Parse GitHub Actions run logs and detect errors
2. Diagnose failures with Gemini / Groq AI
3. Apply known auto-fixes directly to the codebase (commits to repo)
4. Improve YouTube content quality proactively
5. Send a daily report (Make.com webhook + GitHub Issue + Reddit notification)

Usage:
  python tools/pipeline_doctor.py --mode full        # Full maintenance cycle
  python tools/pipeline_doctor.py --mode diagnose    # Diagnose only
  python tools/pipeline_doctor.py --mode report      # Generate & send report only
  python tools/pipeline_doctor.py --mode improve     # YT quality improvement only
  python tools/pipeline_doctor.py --dry-run          # Simulate without writes
"""

import os
import sys
import re
import io
import json
import time
import zipfile
import logging
import argparse
import subprocess
import traceback
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests

# ─── PATHS ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
HEALTH_FILE = DATA_DIR / "pipeline_health.json"
CORE_DIR = BASE_DIR / "core"
GEMINI_GEN_FILE = CORE_DIR / "gemini_generators.py"

sys.path.append(str(BASE_DIR))
sys.path.append(str(CORE_DIR))

# ─── ENV ─────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("MaintenanceAgent")

# -- AGENT MODE FLAG --
AGENT_MODE = False

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
REPO = os.getenv("GITHUB_REPOSITORY", "amazingcoolfinds/amazingcoolfindsauto")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://amazing-cool-finds.com")
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CF_WORKER_NAME = "article-generator" # Adjust based on real name
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()

GH_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
GH_API = f"https://api.github.com/repos/{REPO}"

# ─── KNOWN AUTO-FIXES ────────────────────────────────────────────────────────
# Each entry: (error_pattern, fix_id, description)
KNOWN_FIXES = [
    (r"No module named 'yaml'",           "add_pyyaml",         "Add pyyaml to requirements.txt"),
    (r"No module named 'pyyaml'",         "add_pyyaml",         "Add pyyaml to requirements.txt"),
    (r"429.*quota|quota.*exceeded",       "gemini_quota_retry",  "Increase Gemini retry delay + wait time"),
    (r"No strategic products found",      "lower_min_price",     "Lower min_price threshold in pipeline"),
    (r"playwright.*timeout|timeout.*playwright", "playwright_timeout", "Increase Playwright timeout"),
    (r"No products found at \$\d+",       "lower_min_price",     "Lower min_price threshold in pipeline"),
    (r"CriticalPipelineError.*voice|voice.*CriticalPipelineError", "log_groq_missing", "Log Groq voice issue — check GROQ_API_KEY"),
    (r"Connection.*refused|ConnectionError", "network_retry",   "Add retry logic for network errors"),
]


# ══════════════════════════════════════════════════════════════════════════════
#  HEALTH TRACKER
# ══════════════════════════════════════════════════════════════════════════════

def load_health() -> dict:
    """Load pipeline health history from disk. Handles legacy list format."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if HEALTH_FILE.exists():
        try:
            with open(HEALTH_FILE) as f:
                data = json.load(f)
            # Migrate legacy format: if the file is a plain list, wrap it
            if isinstance(data, list):
                log.info("⚙️  Migrating legacy pipeline_health.json list → dict format")
                return {"runs": data, "fixes_applied": [], "yt_improvements": []}
            if isinstance(data, dict):
                # Ensure all required keys exist
                data.setdefault("runs", [])
                data.setdefault("fixes_applied", [])
                data.setdefault("yt_improvements", [])
                return data
        except Exception as e:
            log.warning(f"⚠️  Could not load health file: {e}")
    return {"runs": [], "fixes_applied": [], "yt_improvements": []}


def save_health(health: dict):
    """Persist health data to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    health["runs"] = health.get("runs", [])[-100:]       # Keep last 100 runs
    health["fixes_applied"] = health.get("fixes_applied", [])[-50:]
    health["yt_improvements"] = health.get("yt_improvements", [])[-50:]
    with open(HEALTH_FILE, "w") as f:
        json.dump(health, f, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
#  GITHUB ACTIONS — LOG FETCHING
# ══════════════════════════════════════════════════════════════════════════════

def get_workflow_runs(workflow_name="Daily Product Pipeline", limit=10) -> list:
    """Fetch recent workflow runs from GitHub API."""
    try:
        resp = requests.get(
            f"{GH_API}/actions/runs",
            headers=GH_HEADERS,
            params={"per_page": limit},
            timeout=15
        )
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        if workflow_name:
            runs = [r for r in runs if workflow_name in r.get("name", "")]
        return runs
    except Exception as e:
        log.error(f"❌ Failed to fetch runs: {e}")
        return []


def fetch_run_logs(run_id: int) -> str:
    """
    Download the ZIP logs for a run, extract & return relevant error text.
    GitHub returns a redirect to a pre-signed S3 URL.
    """
    try:
        resp = requests.get(
            f"{GH_API}/actions/runs/{run_id}/logs",
            headers=GH_HEADERS,
            allow_redirects=True,
            timeout=60
        )
        if resp.status_code != 200:
            return f"⚠️ Could not download logs (HTTP {resp.status_code})"

        z = zipfile.ZipFile(io.BytesIO(resp.content))
        all_lines = []
        for name in z.namelist():
            if name.endswith(".txt"):
                raw = z.read(name).decode("utf-8", errors="replace")
                all_lines.extend(raw.splitlines())

        # Filter to keep only relevant lines (errors, warnings, key steps)
        relevant = []
        keywords = ["error", "warning", "exception", "failed", "critical",
                    "traceback", "❌", "⚠️", "🛑", "step", "success", "✅"]
        for line in all_lines:
            ll = line.lower()
            if any(kw in ll for kw in keywords):
                relevant.append(line.strip())

        return "\n".join(relevant[-300:]) if relevant else "\n".join(all_lines[-200:])

    except Exception as e:
        return f"⚠️ Log parsing error: {e}"


def get_run_jobs_summary(run_id: int) -> dict:
    """Get job-level failure details for a run."""
    try:
        resp = requests.get(
            f"{GH_API}/actions/runs/{run_id}/jobs",
            headers=GH_HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])
        summary = {}
        for job in jobs:
            failed_steps = [
                s["name"] for s in job.get("steps", [])
                if s.get("conclusion") == "failure"
            ]
            summary[job["name"]] = {
                "conclusion": job.get("conclusion"),
                "failed_steps": failed_steps
            }
        return summary
    except Exception as e:
        log.warning(f"⚠️ Could not get job summary: {e}")
        return {}


# ══════════════════════════════════════════════════════════════════════════════
#  CLOUDFLARE MONITORING
# ══════════════════════════════════════════════════════════════════════════════

def fetch_cloudflare_worker_health() -> dict:
    """Check Cloudflare Worker health (via API or recent activity)."""
    if not CF_API_TOKEN or not CF_ACCOUNT_ID:
        return {"status": "unknown", "message": "Cloudflare credentials missing"}

    try:
        # Check KV for last article timestamp as a health proxy
        # Or check Worker status via API
        resp = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/workers/scripts/{CF_WORKER_NAME}",
            headers={"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"},
            timeout=15
        )
        if resp.status_code == 200:
            return {"status": "ok", "message": "Worker is active and configured"}
        else:
            return {"status": "error", "message": f"Cloudflare API error: {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  AI DIAGNOSIS
# ══════════════════════════════════════════════════════════════════════════════

def call_ai(prompt: str, model_pref: str = "gemini") -> str:
    """Call Gemini (primary) or Groq (fallback) with the given prompt."""
    # Try Kimi via NVIDIA (User preferred)
    if NVIDIA_API_KEY and model_pref == "kimi":
        try:
            resp = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-ai/deepseek-v3", # Kimi k2.5 is often a DeepSeek v3 variant or similar on Nvidia
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 1024
                },
                timeout=30
            )
            if resp.ok:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                log.warning(f"🏔️ Kimi (NVIDIA) failed with status {resp.status_code}. Trying Gemini...")
        except Exception as e:
            log.warning(f"🏔️ Kimi (NVIDIA) call failed: {e}. Trying Gemini...")

    # Try Gemini next
    if GEMINI_API_KEY and (model_pref == "gemini" or model_pref == "kimi"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            log.warning(f"💎 Gemini AI call failed: {e}. Trying Groq...")

    # Fallback: Groq
    if GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            result = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            return result.choices[0].message.content
        except Exception as e:
            log.error(f"🧠 Groq AI call also failed: {e}")

    return "⚠️ No AI available for analysis."


def diagnose_with_ai(log_text: str, run_meta: dict) -> dict:
    """
    Send log text to AI for structured diagnosis.
    Returns: {error_type, root_cause, fix_recommendation, severity, yt_impact}
    """
    prompt = f"""You are the 'Pipeline Doctor' for AmazingCoolFinds — an automated Amazon product scraping, 
video generation, and YouTube upload pipeline. You diagnose failures and propose actionable fixes.

PIPELINE OVERVIEW:
- enhanced_pipeline.py: Scrapes Amazon products, generates AI scripts (Gemini), voiceovers (Groq), MP4 videos, uploads to YouTube/Meta/TikTok
- Runs every 12h via GitHub Actions (00:00 UTC and 12:00 UTC)
- Critical path: Product Discovery → Gemini Script → Groq Voiceover → Video → YouTube Upload

RUN METADATA:
- Run ID: {run_meta.get('run_id')}
- Status: {run_meta.get('conclusion')}
- Run URL: {run_meta.get('url')}

FILTERED LOGS (most recent errors/warnings):
{log_text[:4000]}

Provide a concise diagnosis in this EXACT JSON format (no markdown, pure JSON):
{{
  "error_type": "one of: gemini_quota | groq_quota | no_products_found | playwright_timeout | network_error | yaml_missing | auth_error | video_generation | other",
  "root_cause": "1-2 sentence root cause explanation",
  "fix_recommendation": "specific, actionable fix — include code snippet if applicable",
  "severity": "critical | high | medium | low",
  "yt_impact": "how this failure affects YouTube view generation",
  "prevention": "how to prevent this in the future"
}}"""

    # Prefer Kimi (NVIDIA) for diagnosis if available
    model_choice = "kimi" if NVIDIA_API_KEY else "gemini"
    raw = call_ai(prompt, model_pref=model_choice)
    try:
        # Extract JSON from response
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return {
        "error_type": "other",
        "root_cause": raw[:300] if raw else "AI diagnosis unavailable",
        "fix_recommendation": "Manual investigation required",
        "severity": "high",
        "yt_impact": "Unknown — review logs manually",
        "prevention": "Set up better error alerting"
    }


# ══════════════════════════════════════════════════════════════════════════════
#  AUTO-FIX ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def detect_errors(log_text: str) -> list:
    """Scan log text against known error patterns and return matched fix IDs."""
    matches = []
    for pattern, fix_id, desc in KNOWN_FIXES:
        if re.search(pattern, log_text, re.IGNORECASE):
            if fix_id not in [m[0] for m in matches]:
                matches.append((fix_id, desc))
    return matches


def apply_fix(fix_id: str, dry_run: bool = False) -> dict:
    """Apply a known fix. Returns {applied, description, changed_files}."""
    result = {"applied": False, "description": "", "changed_files": []}

    if fix_id == "add_pyyaml":
        req_file = BASE_DIR / "requirements.txt"
        content = req_file.read_text()
        if "pyyaml" not in content.lower():
            if not dry_run:
                with open(req_file, "a") as f:
                    f.write("\npyyaml>=6.0.0\n")
            result.update({"applied": True, "description": "Added pyyaml to requirements.txt", "changed_files": ["requirements.txt"]})
        else:
            result.update({"applied": False, "description": "pyyaml already in requirements.txt"})

    elif fix_id == "gemini_quota_retry":
        # Increase the retry sleep time in gemini_generators.py
        if GEMINI_GEN_FILE.exists():
            content = GEMIMI_GEN_FILE_content = GEMINI_GEN_FILE.read_text()
            # Find "time.sleep(2)" in retry loop and bump to 5
            new_content = re.sub(r'time\.sleep\(2\)', 'time.sleep(5)', content, count=1)
            if new_content != content:
                if not dry_run:
                    GEMINI_GEN_FILE.write_text(new_content)
                result.update({"applied": True, "description": "Increased Gemini retry sleep from 2s → 5s", "changed_files": ["core/gemini_generators.py"]})
            else:
                result.update({"applied": False, "description": "Gemini retry delay already optimized"})

    elif fix_id == "lower_min_price":
        pipeline_file = BASE_DIR / "enhanced_pipeline.py"
        content = pipeline_file.read_text()
        # Lower the min_price in price_thresholds if 30 is not already the minimum
        if "[60, 45, 30]" in content:
            new_content = content.replace("[60, 45, 30]", "[50, 35, 20]")
            if not dry_run:
                pipeline_file.write_text(new_content)
            result.update({"applied": True, "description": "Lowered price thresholds: [60,45,30] → [50,35,20]", "changed_files": ["enhanced_pipeline.py"]})
        elif "[50, 35, 20]" in content:
            result.update({"applied": False, "description": "Price already at lower threshold [50,35,20]"})
        else:
            result.update({"applied": False, "description": "Could not locate price threshold array — manual review needed"})

    elif fix_id == "playwright_timeout":
        scraper_file = CORE_DIR / "advanced_scraper.py"
        if scraper_file.exists():
            content = scraper_file.read_text()
            # Add/increase timeout in page.goto calls
            new_content = re.sub(
                r'page\.goto\(([^)]+)\)',
                lambda m: m.group(0) if 'timeout' in m.group(0) else m.group(0).rstrip(')') + ', timeout=60000)',
                content
            )
            if new_content != content:
                if not dry_run:
                    scraper_file.write_text(new_content)
                result.update({"applied": True, "description": "Added 60s timeout to Playwright page.goto calls", "changed_files": ["core/advanced_scraper.py"]})
            else:
                result.update({"applied": False, "description": "Playwright timeouts already configured"})

    elif fix_id == "log_groq_missing":
        result.update({
            "applied": False,
            "description": "⚠️ ACTION REQUIRED: GROQ_API_KEY may be missing or quota exceeded. Check GitHub Secrets → GROQ_API_KEY",
            "changed_files": []
        })

    elif fix_id == "network_retry":
        result.update({
            "applied": False,
            "description": "Network connection error detected. This is transient — will auto-retry on next scheduled run.",
            "changed_files": []
        })

    return result


def git_commit_fixes(changed_files: list, fix_descriptions: list, dry_run: bool = False) -> bool:
    """Stage and commit auto-fix changes to the repository."""
    if dry_run or not changed_files:
        return False

    try:
        # Configure git identity (required in CI)
        subprocess.run(["git", "config", "user.email", "agent@amazingcoolfinds.bot"], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "config", "user.name", "Pipeline Maintenance Agent"], cwd=BASE_DIR, check=True)

        # Stage changed files
        for f in changed_files:
            subprocess.run(["git", "add", f], cwd=BASE_DIR, check=True)

        # Commit
        commit_msg = "🤖 Auto-fix: " + " | ".join(fix_descriptions[:3])
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=True)

        # Push
        subprocess.run(["git", "push"], cwd=BASE_DIR, check=True)
        log.info(f"✅ Auto-fix committed and pushed: {commit_msg}")
        return True

    except subprocess.CalledProcessError as e:
        log.warning(f"⚠️ Git commit failed (may be nothing to commit): {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  YOUTUBE QUALITY IMPROVEMENT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_yt_quality(products: list) -> dict:
    """Evaluate YouTube content quality metrics from recent processed products."""
    if not products:
        return {"score": 0, "issues": ["No products data available"], "suggestions": []}

    hook_types = []
    hook_patterns = {
        "pain_point": r"drive you crazy|frustrat|annoy|tired of",
        "bold_prediction": r"literally going to|will change|transform",
        "curiosity_gap": r"most people don't|secret|didn't know",
        "visual_hook": r"i wasn't expecting|surprised|wow",
        "gift_idea": r"perfect gift|looking for.*gift",
        "pov": r"^pov:",
        "life_hack": r"hack that|trick that|works every time"
    }

    issues = []
    for p in products:
        script = p.get("script", {})
        narration = script.get("narration", "").lower() if isinstance(script, dict) else ""
        matched = False
        for hook_name, pattern in hook_patterns.items():
            if re.search(pattern, narration[:100], re.IGNORECASE):
                hook_types.append(hook_name)
                matched = True
                break
        if not matched:
            hook_types.append("unknown")

        # Check for forbidden openers
        if narration.startswith("you need to see") or narration.startswith("check this out"):
            issues.append(f"Forbidden hook opener detected in ASIN {p.get('asin', '?')}")

    # Analyze hook diversity
    from collections import Counter
    hook_counts = Counter(hook_types)
    total = len(hook_types)
    dominant = hook_counts.most_common(1)[0] if hook_counts else ("unknown", 0)

    diversity_score = len([h for h, c in hook_counts.items() if c >= 1]) / max(len(hook_patterns), 1)
    score = int(diversity_score * 100)

    suggestions = []
    if dominant[1] / max(total, 1) > 0.5:
        suggestions.append(f"Hook type '{dominant[0]}' is overused ({dominant[1]}/{total} scripts). Increase variety.")
    if "unknown" in hook_counts and hook_counts["unknown"] / max(total, 1) > 0.3:
        suggestions.append("Many scripts have unrecognized hook structure — AI prompt may need strengthening.")
    if total < 2:
        suggestions.append("Not enough recent scripts to evaluate diversity (fewer than 2 products processed).")

    return {
        "score": score,
        "total_scripts_analyzed": total,
        "hook_distribution": dict(hook_counts),
        "issues": issues,
        "suggestions": suggestions
    }


def apply_yt_improvement(quality_report: dict, dry_run: bool = False) -> list:
    """Apply prompt improvements to gemini_generators.py based on quality report."""
    improvements = []
    if not quality_report.get("suggestions"):
        return improvements

    if not GEMINI_GEN_FILE.exists():
        return improvements

    content = GEMINI_GEN_FILE.read_text()

    # If hook diversity score is below 60, reinforce the hook variety directive
    if quality_report.get("score", 100) < 60:
        old_directive = '"   - POV: \'POV: You just found the missing piece for your [Category] setup.\'\\n"'
        # Add a temperature boost note after the hook section
        boost_note = (
            '"   - Shock Value: \'Wait — this [Product] costs HOW MUCH? And it still sold out?\'\\n"'
        )
        if "Shock Value" not in content:
            new_content = content.replace(
                '\"   - POV: \'POV: You just found the missing piece for your [Category] setup.\'\\n\"',
                '\"   - POV: \'POV: You just found the missing piece for your [Category] setup.\'\\n\"\n            ' + boost_note
            )
            if new_content != content:
                if not dry_run:
                    GEMINI_GEN_FILE.write_text(new_content)
                improvements.append("Added 'Shock Value' hook variant to Gemini prompt for better diversity")

    # If forbidden openers detected, strengthen the prohibition
    if quality_report.get("issues"):
        forbidden_issues = [i for i in quality_report["issues"] if "Forbidden hook" in i]
        if forbidden_issues and "STRICTLY FORBIDDEN" not in content:
            # Add stronger prohibition
            old_line = '"1. THE HOOK (Scroll-Stopper): NEVER start with \'Check this out\' or \'You need this\'.'
            new_line = (
                '"1. THE HOOK (Scroll-Stopper): STRICTLY FORBIDDEN openers: \'Check this out\', '
                '\'You need this\', \'You need to see\', \'Look at this\'. '
                'ANY script starting with these phrases will be REJECTED.'
            )
            if old_line in content:
                new_content = content.replace(old_line, new_line)
                if not dry_run:
                    GEMINI_GEN_FILE.write_text(new_content)
                improvements.append("Strengthened forbidden hook prohibition in Gemini prompt")

    return improvements


def load_recent_products() -> list:
    """Load recently processed products from data files."""
    for path in [BASE_DIR / "amazing" / "data" / "products.json", DATA_DIR / "products.json"]:
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                # Return last 10 most recent products that have scripts
                products_with_scripts = [p for p in data if p.get("script")]
                return products_with_scripts[-10:]
            except Exception:
                pass
    return []


# ══════════════════════════════════════════════════════════════════════════════
#  DAILY REPORT GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def get_runs_today(health: dict) -> list:
    """Return all run records for today."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [r for r in health.get("runs", []) if r.get("date") == today]


def get_7day_metrics(health: dict) -> dict:
    """Compute 7-day rolling metrics."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent = []
    for r in health.get("runs", []):
        try:
            ts = datetime.fromisoformat(r.get("timestamp", "").replace("Z", "+00:00"))
            if ts >= cutoff:
                recent.append(r)
        except Exception:
            pass

    total = len(recent)
    successes = sum(1 for r in recent if r.get("conclusion") == "success")
    yt_uploads = sum(r.get("youtube_uploaded", 0) for r in recent)
    products = sum(r.get("products_processed", 0) for r in recent)

    return {
        "total_runs": total,
        "success_rate": f"{int(successes/max(total,1)*100)}%",
        "videos_per_day": round(yt_uploads / 7, 1),
        "products_per_day": round(products / 7, 1),
        "yt_uploads_7d": yt_uploads
    }


def format_run_block(run: dict, label: str) -> str:
    """Format a single run result for the daily report."""
    status_icon = "✅" if run.get("conclusion") == "success" else "❌"
    errors_txt = "\n    ".join(run.get("errors", ["None"])) or "None"
    return f"""
⏰ {label}
  {status_icon} Status: {run.get('conclusion', 'unknown').upper()}
  📦 Productos procesados: {run.get('products_processed', 0)}
  🎬 Videos generados: {run.get('videos_generated', 0)}
  📹 YouTube uploads: {run.get('youtube_uploaded', 0)}
  🕒 Timestamp: {run.get('timestamp', 'N/A')}
  ❌ Errores: {errors_txt}
  🔗 Run URL: {run.get('url', 'N/A')}"""


def generate_daily_report(health: dict) -> str:
    """Generate the full daily markdown report."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_runs = get_runs_today(health)
    metrics_7d = get_7day_metrics(health)
    fixes_today = [f for f in health.get("fixes_applied", []) if f.get("date") == today_str]
    improvements_today = [i for i in health.get("yt_improvements", []) if i.get("date") == today_str]

    # Build run blocks
    run1_block = format_run_block(today_runs[0], "ACTIVACIÓN 1 (00:00 UTC)") if len(today_runs) > 0 else "\n⏰ ACTIVACIÓN 1 (00:00 UTC)\n  ⚠️ Sin datos registrados para esta activación."
    run2_block = format_run_block(today_runs[1], "ACTIVACIÓN 2 (12:00 UTC)") if len(today_runs) > 1 else "\n⏰ ACTIVACIÓN 2 (12:00 UTC)\n  ⏳ Aún no ejecutada o sin datos."

    # Auto-fixes block
    fixes_txt = "\n".join([f"  🔧 {f.get('description', 'Fix applied')}" for f in fixes_today]) or "  ✅ Ningún fix necesario hoy"

    # YT improvements block
    improvements_txt = "\n".join([f"  📈 {i.get('description', 'Improvement applied')}" for i in improvements_today]) or "  ✅ La calidad de scripts YT está en niveles óptimos"

    # Cloudflare block
    last_run = today_runs[-1] if today_runs else (health.get("runs")[-1] if health.get("runs") else {})
    cf_status = last_run.get("cloudflare_health", {"status": "unknown", "message": "No data"})
    cf_icon = "✅" if cf_status.get("status") == "ok" else ("❌" if cf_status.get("status") == "error" else "⚪")
    cf_txt = f"  {cf_icon} Worker: {CF_WORKER_NAME}\n  💬 Estado: {cf_status.get('message')}"

    # Overall health
    overall_today = "✅ SALUDABLE" if all(r.get("conclusion") == "success" for r in today_runs) and today_runs else ("❌ CON ERRORES" if any(r.get("conclusion") == "failure" for r in today_runs) else "⏳ INCOMPLETO")

    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 INFORME DIARIO — AmazingCoolFinds Pipeline
Fecha: {today_str}  |  Estado: {overall_today}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{run1_block}
{run2_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 FIXES AUTOMÁTICOS APLICADOS HOY
{fixes_txt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 MEJORAS DE CALIDAD YOUTUBE IMPLEMENTADAS
{improvements_txt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 ESTADO DE CLOUDFLARE (Article Generator)
{cf_txt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 MÉTRICAS ÚLTIMOS 7 DÍAS
  🏃 Total runs: {metrics_7d['total_runs']}
  ✅ Tasa de éxito: {metrics_7d['success_rate']}
  🎬 Videos/día promedio: {metrics_7d['videos_per_day']}
  📦 Productos/día promedio: {metrics_7d['products_per_day']}
  📹 Total YouTube uploads (7d): {metrics_7d['yt_uploads_7d']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agente de Mantenimiento AmazingCoolFinds v2.0
   Repositorio: https://github.com/{REPO}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return report.strip()


# ══════════════════════════════════════════════════════════════════════════════
#  NOTIFICATION DELIVERY
# ══════════════════════════════════════════════════════════════════════════════

def send_via_make_webhook(report: str, title: str = "Daily Pipeline Report") -> bool:
    """Send report to Make.com webhook (connects to email/Slack/Notion etc.)."""
    if not MAKE_WEBHOOK_URL or "your_webhook" in MAKE_WEBHOOK_URL:
        log.info("ℹ️  Make.com webhook not configured — skipping.")
        return False
    try:
        resp = requests.post(
            MAKE_WEBHOOK_URL,
            json={"title": title, "report": report, "timestamp": datetime.now(timezone.utc).isoformat()},
            timeout=15
        )
        if resp.ok:
            log.info("✅ Report sent via Make.com webhook")
            return True
        else:
            log.warning(f"⚠️ Make.com webhook returned {resp.status_code}")
            return False
    except Exception as e:
        log.error(f"❌ Make.com webhook error: {e}")
        return False


def create_github_issue(title: str, body: str) -> bool:
    """Create a GitHub Issue with the report as fallback notification."""
    if not GITHUB_TOKEN:
        log.warning("⚠️ No GITHUB_TOKEN for issue creation")
        return False
    try:
        resp = requests.post(
            f"{GH_API}/issues",
            headers=GH_HEADERS,
            json={"title": title, "body": body, "labels": ["pipeline-report"]},
            timeout=15
        )
        if resp.status_code == 201:
            issue = resp.json()
            log.info(f"✅ GitHub Issue created: {issue.get('html_url')}")
            return True
        else:
            log.warning(f"⚠️ Issue creation failed: {resp.status_code} — {resp.text[:200]}")
            return False
    except Exception as e:
        log.error(f"❌ GitHub Issue error: {e}")
        return False


def post_to_reddit_via_webhook(report: str, title: str) -> bool:
    """
    Post daily summary to Reddit using Make.com webhook or the pipeline's Make integration.
    The Cloudflare Worker already handles Reddit posting; we trigger via Make.com.
    If Make.com isn't configured, we attempt direct Reddit API post.
    """
    reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_secret = os.getenv("REDDIT_SECRET", "")
    reddit_username = os.getenv("REDDIT_USERNAME", "")
    reddit_password = os.getenv("REDDIT_PASSWORD", "")
    reddit_subreddit = os.getenv("REDDIT_SUBREDDIT", "")

    if not all([reddit_client_id, reddit_secret, reddit_username, reddit_password, reddit_subreddit]):
        log.info("ℹ️  Reddit credentials not available in this environment — skipping Reddit notification.")
        return False

    try:
        # 1. Authenticate
        auth_resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(reddit_client_id, reddit_secret),
            data={"grant_type": "password", "username": reddit_username, "password": reddit_password},
            headers={"User-Agent": f"AmazingCoolFindsBot/2.0 by {reddit_username}"},
            timeout=15
        )
        token_data = auth_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            log.warning("⚠️ Reddit auth failed — no access token")
            return False

        # 2. Convert markdown report to Reddit-friendly post
        reddit_body = (
            f"**Reporte automático del pipeline AmazingCoolFinds**\n\n"
            f"```\n{report[:900]}\n```\n\n"
            f"[Ver pipeline en GitHub](https://github.com/{REPO}/actions)"
        )

        # 3. Submit
        submit_resp = requests.post(
            "https://oauth.reddit.com/api/submit",
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": f"AmazingCoolFindsBot/2.0 by {reddit_username}"
            },
            data={
                "sr": reddit_subreddit,
                "kind": "self",
                "title": title,
                "text": reddit_body,
                "nsfw": False
            },
            timeout=15
        )

        result = submit_resp.json()
        # Check for errors in the Reddit API response JSON
        errors = result.get("json", {}).get("errors", [])
        if not errors:
            log.info(f"✅ Daily report posted to r/{reddit_subreddit} on Reddit")
            return True
        else:
            log.warning(f"⚠️ Reddit post returned errors: {errors}")
            return False

    except Exception as e:
        log.error(f"❌ Reddit post error: {e}")
        return False


def deliver_report(report: str, today_runs: list):
    """Deliver the daily report through all available channels."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    has_failure = any(r.get("conclusion") == "failure" for r in today_runs)
    status_emoji = "❌" if has_failure else "✅"
    title = f"{status_emoji} AmazingCoolFinds Pipeline Report — {today_str}"

    delivered = False

    # Channel 1: Make.com webhook (primary)
    if send_via_make_webhook(report, title):
        delivered = True

    # Channel 2: Reddit (if configured)
    if post_to_reddit_via_webhook(report, title):
        delivered = True

    # Channel 3: GitHub Issue (fallback — always try if nothing else worked)
    if not delivered or has_failure:
        create_github_issue(title, f"```\n{report}\n```")

    log.info(f"📬 Report delivery complete. Channels attempted: Make.com, Reddit, GitHub Issues")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN AGENT MODES
# ══════════════════════════════════════════════════════════════════════════════

def mode_diagnose(health: dict, run_id: int = None, conclusion: str = None, dry_run: bool = False) -> dict:
    """Diagnose the latest (or specified) pipeline run."""
    log.info("🩺 MODE: DIAGNOSE — Analyzing pipeline run logs...")

    # Get run info
    if run_id:
        runs = [{"id": run_id, "conclusion": conclusion, "html_url": f"https://github.com/{REPO}/actions/runs/{run_id}"}]
    else:
        runs = get_workflow_runs(limit=5)
        if not runs:
            log.error("❌ No runs found to diagnose")
            return {}

    run = runs[0]
    run_id = run.get("id") or run_id
    conclusion = run.get("conclusion") or conclusion
    run_url = run.get("html_url", "")

    log.info(f"📋 Analyzing run {run_id} — conclusion: {conclusion}")

    run_meta = {"run_id": run_id, "conclusion": conclusion, "url": run_url}

    # Fetch real logs
    log.info("📜 Downloading run logs from GitHub Actions...")
    log_text = fetch_run_logs(run_id)
    jobs_summary = get_run_jobs_summary(run_id)
    cf_health = fetch_cloudflare_worker_health()

    # Detect errors
    detected_fixes = detect_errors(log_text)
    log.info(f"🔍 Detected {len(detected_fixes)} auto-fixable error patterns")

    # AI Diagnosis (only on failures)
    diagnosis = {}
    if conclusion == "failure" or conclusion is None:
        log.info("🧠 Sending logs to AI for diagnosis...")
        diagnosis = diagnose_with_ai(log_text, run_meta)
        log.info(f"📝 Diagnosis: {diagnosis.get('error_type', 'unknown')} — {diagnosis.get('severity', 'unknown')} severity")

    # Apply fixes
    applied_fixes = []
    all_changed_files = []
    fix_descriptions = []

    for fix_id, fix_desc in detected_fixes:
        log.info(f"🔧 Applying fix: {fix_desc}...")
        result = apply_fix(fix_id, dry_run=dry_run)
        applied_fixes.append({
            "fix_id": fix_id,
            "description": result["description"],
            "applied": result["applied"],
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
        })
        if result["applied"]:
            all_changed_files.extend(result["changed_files"])
            fix_descriptions.append(result["description"])
            log.info(f"  ✅ {result['description']}")
        else:
            log.info(f"  ℹ️  {result['description']}")

    # Commit fixes to repo
    if all_changed_files and not dry_run:
        git_commit_fixes(all_changed_files, fix_descriptions, dry_run=dry_run)

    # Build run record for health file
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    existing_today = [r for r in health.get("runs", []) if r.get("date") == today_str]
    run_number = len(existing_today) + 1

    # Try to extract metrics from log text
    products_match = re.search(r'Found (\d+) strategic candidates', log_text)
    success_match = re.search(r'Successes:\s*(\d+)', log_text)
    yt_match = re.search(r'YouTube metadata saved|youtube_uploaded.*True', log_text)

    error_lines = [l for l in log_text.splitlines() if re.search(r'❌|🛑|ERROR', l)][:5]

    run_record = {
        "run_id": run_id,
        "date": today_str,
        "run_number_today": run_number,
        "conclusion": conclusion,
        "products_processed": int(success_match.group(1)) if success_match else 0,
        "videos_generated": int(success_match.group(1)) if success_match else 0,
        "youtube_uploaded": 1 if yt_match else 0,
        "errors": error_lines,
        "diagnosis": diagnosis,
        "fixes_detected": [f[1] for f in detected_fixes],
        "cloudflare_health": cf_health,
        "url": run_url,
        "timestamp": now.isoformat()
    }

    health.setdefault("runs", []).append(run_record)
    health.setdefault("fixes_applied", []).extend(applied_fixes)
    save_health(health)

    log.info(f"✅ Diagnose complete. Run #{run_number} for today recorded.")
    return run_record


def mode_improve(health: dict, dry_run: bool = False) -> list:
    """Evaluate and improve YouTube content quality."""
    log.info("📈 MODE: IMPROVE — Evaluating YouTube output quality...")

    products = load_recent_products()
    quality = evaluate_yt_quality(products)

    log.info(f"📊 YT Quality Score: {quality['score']}/100")
    log.info(f"🎣 Hook distribution: {quality.get('hook_distribution', {})}")

    for issue in quality.get("issues", []):
        log.warning(f"  ⚠️ {issue}")
    for suggestion in quality.get("suggestions", []):
        log.info(f"  💡 {suggestion}")

    # Apply improvements
    improvements = apply_yt_improvement(quality, dry_run=dry_run)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    improvement_records = [
        {"description": imp, "date": today_str, "quality_score": quality["score"]}
        for imp in improvements
    ]

    if improvement_records and not dry_run:
        health.setdefault("yt_improvements", []).extend(improvement_records)
        save_health(health)
        # Commit quality improvements
        if GEMINI_GEN_FILE.exists():
            git_commit_fixes(["core/gemini_generators.py"], [i["description"] for i in improvement_records], dry_run=dry_run)

    if improvements:
        log.info(f"✅ Applied {len(improvements)} YT quality improvement(s)")
    else:
        log.info("✅ No YT quality improvements needed at this time")

    return improvement_records


def mode_report(health: dict):
    """Generate and deliver the daily report."""
    log.info("📊 MODE: REPORT — Generating daily pipeline report...")

    today_runs = get_runs_today(health)
    report = generate_daily_report(health)

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60 + "\n")

    if not AGENT_MODE:
        deliver_report(report, today_runs)


def mode_full(health: dict, run_id: int = None, conclusion: str = None,
              run_number: int = None, dry_run: bool = False):
    """Full maintenance cycle: diagnose + improve + report (if 2nd run of day)."""
    log.info("🚀 MODE: FULL — Running complete maintenance cycle...")

    # Step 1: Diagnose
    mode_diagnose(health, run_id=run_id, conclusion=conclusion, dry_run=dry_run)

    # Reload health after diagnose (file was updated)
    health = load_health()

    # Step 2: YT Quality Improvement
    mode_improve(health, dry_run=dry_run)

    # Reload health again
    health = load_health()

    # Step 3: Send daily report only on 2nd run of the day (or if explicitly forced)
    today_runs = get_runs_today(health)
    log.info(f"📅 Runs recorded today: {len(today_runs)}")

    if len(today_runs) >= 2 or run_number == 2:
        log.info("📬 2nd run of day detected — sending daily report...")
        mode_report(health)
    else:
        log.info("ℹ️  Only 1st run today — report will be sent after 2nd activation at 12:00 UTC")


# ══════════════════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AmazingCoolFinds Pipeline Maintenance Agent v2.0")
    parser.add_argument("--mode", choices=["full", "diagnose", "report", "improve"], default="full")
    parser.add_argument("--run-id", type=int, help="GitHub Actions Run ID to diagnose")
    parser.add_argument("--conclusion", help="Run conclusion (success/failure)")
    parser.add_argument("--run-number", type=int, help="Which daily run this is (1 or 2)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing or committing changes")
    parser.add_argument("--agent-mode", action="store_true", help="Output results in JSON format for the Sentinel agent")

    # Legacy support
    parser.add_argument("--diagnose", action="store_true", help="Alias for --mode diagnose")
    parser.add_argument("--improve", action="store_true", help="Alias for --mode improve")
    parser.add_argument("--auto-fix", action="store_true", help="Alias for --mode full")

    args = parser.parse_args()

    # Handle legacy flags
    if args.diagnose:
        args.mode = "diagnose"
    elif args.improve:
        args.mode = "improve"
    elif args.auto_fix:
        args.mode = "full"

    if args.dry_run:
        log.info("🔬 DRY RUN MODE — No files will be modified or committed")

    health = load_health()

    try:
        if args.agent_mode:
            AGENT_MODE = True
            # Silence regular logging for clean JSON output
            logging.getLogger().setLevel(logging.ERROR)

        result_data = {}
        if args.mode == "full":
            result_data = mode_full(health, run_id=args.run_id, conclusion=args.conclusion,
                                     run_number=args.run_number, dry_run=args.dry_run)
        elif args.mode == "diagnose":
            result_data = mode_diagnose(health, run_id=args.run_id, conclusion=args.conclusion, dry_run=args.dry_run)
        elif args.mode == "improve":
            result_data = mode_improve(health, dry_run=args.dry_run)
        elif args.mode == "report":
            result_data = {"report": generate_daily_report(health), "today_runs": get_runs_today(health)}
            mode_report(health)

        if args.agent_mode:
            print("\n---SENTINEL_JSON_START---")
            print(json.dumps(result_data, indent=2, default=str))
            print("---SENTINEL_JSON_END---")

        log.info("🏁 Maintenance Agent completed successfully.")

    except Exception as e:
        log.error(f"💥 Agent crashed: {e}")
        log.error(traceback.format_exc())
        sys.exit(1)
