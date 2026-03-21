#!/usr/bin/env python3
"""
🤖 Sentinel Agent - AmazingCoolFinds
===================================
Autonomous AI agent powered by Gemini.
Uses reasoning to answer questions and improve the pipeline.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("Sentinel")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MEMORY_FILE = DATA_DIR / "sentinel_memory.json"
HEALTH_FILE = DATA_DIR / "pipeline_health.json"
IMPROVEMENT_FILE = DATA_DIR / "improvement_queue.json"
QUESTION_FILE = DATA_DIR / "telegram_question.txt"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
REPO = os.getenv("GITHUB_REPOSITORY", "amazingcoolfinds/amazingcoolfindsauto")

GH_API = f"https://api.github.com/repos/{REPO}"
GH_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"last_heartbeat": None, "health_trends": {}, "issues_tracked": [], "improvements_queued": []}

def save_memory(memory):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def load_health():
    if HEALTH_FILE.exists():
        try:
            with open(HEALTH_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"runs": [], "fixes_applied": [], "yt_improvements": []}

def get_pipeline_runs():
    try:
        resp = requests.get(f"{GH_API}/actions/runs?per_page=5", headers=GH_HEADERS, timeout=15)
        if resp.ok:
            return resp.json().get("workflow_runs", [])
    except Exception as e:
        log.error(f"GitHub API error: {e}")
    return []

def think_with_gemini(question, memory, health):
    """Use Gemini AI to reason about the pipeline and answer questions."""
    if not GEMINI_API_KEY:
        return think_fallback(question, memory, health)
    
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        runs = get_pipeline_runs()
        latest_run = runs[0] if runs else {}
        
        recent_runs = health.get("runs", [])[-10:]
        success_count = sum(1 for r in recent_runs if r.get("conclusion") == "success")
        fail_count = len(recent_runs) - success_count
        total_products = sum(r.get("products_processed", 0) for r in recent_runs)
        
        context = f"""Sentinel Agent - AmazingCoolFinds Pipeline

CURRENT PIPELINE STATUS:
- Latest Run: {latest_run.get('conclusion', 'unknown')} ({latest_run.get('created_at', 'N/A')[:10]})
- Run #{latest_run.get('run_number', '?')}
- Last 10 runs: {success_count} ✅, {fail_count} ❌
- Total products processed (recent): {total_products}

PIPELINE HEALTH:
- Total runs logged: {len(health.get('runs', []))}
- Auto-fixes applied: {len(health.get('fixes_applied', []))}
- YT improvements: {len(health.get('yt_improvements', []))}

MEMORY:
- Last heartbeat: {memory.get('last_heartbeat', 'Never')}
- Issues tracked: {len(memory.get('issues_tracked', []))}

QUESTION FROM USER:
{question}

Respond in Spanish. Be concise but insightful. If the pipeline has issues, suggest specific fixes."""

        response = client.models.generate_content(model="gemini-2.5-flash", contents=context)
        return response.text
        
    except Exception as e:
        log.error(f"Gemini error: {e}")
        return think_fallback(question, memory, health)

def think_fallback(question, memory, health):
    """Fallback logic when Gemini is not available."""
    q = question.lower()
    
    if any(w in q for w in ["status", "estado", "cómo está"]):
        runs = get_pipeline_runs()
        latest = runs[0] if runs else {}
        status = "✅" if latest.get("conclusion") == "success" else "❌" if latest.get("conclusion") == "failure" else "⏳"
        return f"{status} Pipeline {latest.get('conclusion', 'en progreso')}\n📊 Run #{latest.get('run_number', '?')}\n🕒 {latest.get('created_at', '')[:16] if latest.get('created_at') else 'N/A'}"
    
    elif any(w in q for w in ["error", "falla", "problema"]):
        failed = [r for r in get_pipeline_runs() if r.get("conclusion") == "failure"]
        if failed:
            return f"❌ {len(failed)} runs fallaron recientemente. Ejecuta diagnose para analizar."
        return "✅ No hay fallas detectadas en los últimos runs."
    
    elif any(w in q for w in ["video", "youtube"]):
        return "📹 Videos: https://www.youtube.com/@AmazingCoolFinds"
    
    elif any(w in q for w in ["web", "website", "página"]):
        return "🌐 Website: https://amazing-cool-finds.pages.dev"
    
    elif any(w in q for w in ["help", "ayuda", "comandos"]):
        return """🧠 *Comandos:*

• /status - ¿Cómo está el pipeline?
• /sentinel [pregunta] - Pregúntame lo que sea
• /run - Disparar pipeline

Puedo diagnosticar problemas y sugerir mejoras."""
    
    return "🤔 No estoy seguro. Usa /sentinel con tu pregunta."

def mode_full(dry_run=False, question=None, mode="full"):
    memory = load_memory()
    health = load_health()
    
    memory["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    
    if mode == "think" and question:
        response = think_with_gemini(question, memory, health)
    else:
        response = think_with_gemini("Dame un resumen del estado del pipeline", memory, health)
    
    memory["last_summary"] = response
    memory["issues_tracked"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response": response[:200]
    })
    memory["issues_tracked"] = memory["issues_tracked"][-20:]
    
    save_memory(memory)
    
    log.info(f"Response: {response}")
    print(response)
    
    if not dry_run and question:
        send_telegram(response)
    
    return response

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        log.warning("No TELEGRAM_BOT_TOKEN")
        return
    
    if not TELEGRAM_CHAT_ID:
        log.warning("No TELEGRAM_CHAT_ID — cannot send Telegram message")
        return
    
    try:
        msg = message.replace("*", "").replace("_", "")[:4000]
        
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=15
        )
        if resp.ok:
            log.info("✅ Sent to Telegram")
        else:
            log.warning(f"Telegram: {resp.status_code}")
    except Exception as e:
        log.error(f"Telegram failed: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sentinel Agent")
    parser.add_argument("--mode", default="full")
    parser.add_argument("--question", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    mode_full(dry_run=args.dry_run, question=args.question, mode=args.mode)
