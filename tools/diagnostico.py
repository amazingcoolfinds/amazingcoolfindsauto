#!/usr/bin/env python3
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

groq_key = os.getenv("GROQ_API_KEY")
print(f"API Key presente: {'Sí' if groq_key else 'No'}")

try:
    from groq import Groq
    import httpx
    client = Groq(api_key=groq_key, http_client=httpx.Client(trust_env=False))
    models = client.models.list()
    print("\nModelos disponibles en tu cuenta de Groq:")
    for m in models.data:
        print(f" - {m.id}")
except Exception as e:
    print(f"Error consultando Groq: {e}")
