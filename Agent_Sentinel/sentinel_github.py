#!/usr/bin/env python3
"""
🤖 Sentinel Agent - AmazingCoolFinds
===================================
Autonomous agent that lives in GitHub Actions.
Can be triggered by Telegram via Make.com webhook.

Capabilities:
- Diagnose pipeline failures
- Apply auto-fixes
- Answer questions about the pipeline
- Send reports to Telegram
- Update memory files

Usage:
  python Agent_Sentinel/sentinel_github.py --mode full
  python Agent_Sentinel/sentinel_github.py --mode think --question "status?"
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
QUESTION_FILE = DATA_DIR / "telegram_question.txt"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8591494770")
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
    return {
        "last_heartbeat": None,
        "health_trends": {},
        "issues_tracked": [],
        "last_summary": None
    }

def save_memory(memory):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def get_pipeline_status():
    try:
        resp = requests.get(f"{GH_API}/actions/runs?per_page=5", headers=GH_HEADERS, timeout=10)
        if resp.ok:
            runs = resp.json().get("workflow_runs", [])
            latest = runs[0] if runs else None
            if latest:
                status = "✅" if latest.get("conclusion") == "success" else "❌" if latest.get("conclusion") == "failure" else "⏳"
                date = datetime.fromisoformat(latest["created_at"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
                return f"{status} {latest['conclusion'] or 'in_progress'} | {date}\n📊 Run #{latest.get('run_number', '?')}"
    except Exception as e:
        return f"⚠️ Error: {e}"
    return "📭 Sin datos"

def get_recent_health():
    if HEALTH_FILE.exists():
        try:
            with open(HEALTH_FILE) as f:
                health = json.load(f)
            runs = health.get("runs", [])
            if runs:
                last = runs[-1]
                return f"📦 Productos hoy: {last.get('products_processed', 0)}\n📹 YouTube: {last.get('youtube_uploaded', 0)}"
        except:
            pass
    return "📭 Sin datos de salud"

def diagnose_pipeline():
    try:
        resp = requests.get(f"{GH_API}/actions/runs?per_page=3", headers=GH_HEADERS, timeout=10)
        if not resp.ok:
            return "⚠️ No pude acceder a GitHub"
        
        runs = resp.json().get("workflow_runs", [])
        if not runs:
            return "📭 No hay runs recientes"
        
        latest = runs[0]
        conclusion = latest.get("conclusion")
        
        if conclusion == "success":
            return "✅ Pipeline funcionando correctamente"
        elif conclusion == "failure":
            return f"❌ Último pipeline falló: {latest.get('name', 'Unknown')}"
        else:
            return f"⏳ Pipeline en progreso..."
    except Exception as e:
        return f"⚠️ Error: {e}"

def think(question, memory):
    question_lower = question.lower()
    
    if any(w in question_lower for w in ["status", "estado", "cómo está"]):
        status = get_pipeline_status()
        health = get_recent_health()
        return f"📊 *Estado del Pipeline*\n\n{status}\n{health}"
    
    elif any(w in question_lower for w in ["error", "falla", "problema", "broken"]):
        diagnosis = diagnose_pipeline()
        return f"🔍 *Diagnóstico*\n\n{diagnosis}"
    
    elif any(w in question_lower for w in ["video", "youtube", "upload"]):
        return "📹 Los videos se suben a YouTube después de crearse.\n\nPuedes verlos en: https://www.youtube.com/@AmazingCoolFinds"
    
    elif any(w in question_lower for w in ["website", "web", "página"]):
        return "🌐 Website: https://amazing-cool-finds.pages.dev\n\nLos productos se muestran cuando tienen imágenes."
    
    elif any(w in question_lower for w in ["help", "ayuda", "comandos", "commands"]):
        return """🧠 *Comandos de Sentinel*

• /status - Estado del pipeline
• /health - Diagnóstico rápido
• /report - Resumen del día
• /run - Disparar pipeline
• /sentinel [pregunta] - Preguntarme lo que sea"""
    
    else:
        return f"🤔 No entendí: {question}\n\nUsa /sentinel help para ver comandos."

def mode_full(dry_run=False, question=None):
    memory = load_memory()
    memory["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    
    if question:
        response = think(question, memory)
    else:
        diagnosis = diagnose_pipeline()
        status = get_pipeline_status()
        health = get_recent_health()
        response = f"🧠 *Sentinel Heartbeat*\n\n{datetime.now().strftime('%H:%M:%S')}\n\n{status}\n{health}\n\nDiagnóstico: {diagnosis}"
    
    memory["last_summary"] = response
    save_memory(memory)
    
    log.info(f"Response: {response}")
    print(response)
    
    if not dry_run and question:
        send_telegram(response)

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        log.warning("No TELEGRAM_BOT_TOKEN")
        return
    
    try:
        # Escape markdown
        msg = message.replace("*", "").replace("_", "")
        
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=10
        )
        if resp.ok:
            log.info("✅ Message sent to Telegram")
        else:
            log.warning(f"Telegram error: {resp.status_code}")
    except Exception as e:
        log.error(f"Telegram failed: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sentinel Agent")
    parser.add_argument("--mode", default="full")
    parser.add_argument("--question", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    mode_full(dry_run=args.dry_run, question=args.question)
