#!/usr/bin/env python3
"""
Prueba del Módulo 2: Generación de Voz y Video (FFmpeg)
"""
import os
import sys
from pathlib import Path

# Añadir directorios de soporte
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

print("\n" + "="*50)
print("🚀 PROBANDO MÓDULO 2: VOZ + VIDEO (FFMPEG)")
print("="*50 + "\n")

# Datos de prueba (Simulando salida del Módulo 1)
product = {
    "asin": "B0D5BBYRJM",
    "title": "Premium Smart Gadget",
    "price": "$99.99",
    "images": [
        "https://placehold.co/1080x1920/4A90E2/FFF.png?text=Product+Image+1",
        "https://placehold.co/1080x1920/E94B3C/FFF.png?text=Product+Image+2",
        "https://placehold.co/1080x1920/6C5CE7/FFF.png?text=Product+Image+3",
        "https://placehold.co/1080x1920/00B894/FFF.png?text=Product+Image+4",
        "https://placehold.co/1080x1920/FDCB6E/FFF.png?text=Product+Image+5"
    ]
}

script = {
    "title": "Why Is This So Good?!",
    "narration": "Okay, I genuinely did not expect this to be this good. The quality is honestly insane for the price tag. It feels premium, works perfectly, and just makes my life infinitely easier. You have to try this. Link is in the first comment!",
    "hashtags": ["#TikTokMadeMeBuyIt", "#HiddenGems", "#MustHaves", "#ViralFinds"]
}

# 1. Probar Generación de Voz
print("🗣️ 1. Generando voz con Groq/OpenAI...")
voice_path = None
try:
    from groq_generators import GroqVoiceGenerator
    groq_key = os.getenv("GROQ_API_KEY")
    voice_gen = GroqVoiceGenerator(api_key=groq_key)
    voice_path = voice_gen.generate(script["narration"], product["asin"])

    if voice_path and os.path.exists(voice_path):
        print(f"✅ Voz generada con éxito: {voice_path}\n")
    else:
        print("❌ Falló la generación de voz.\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error en generación de voz: {e}\n")
    sys.exit(1)

# 2. Probar Generación de Video
print("🎥 2. Generando video con FFmpeg...")
try:
    from video_generator import VideoGenerator
    video_gen = VideoGenerator()
    video_path = video_gen.generate(product, script, voice_path=str(voice_path))

    if video_path and os.path.exists(video_path):
        print(f"✅ ¡Video generado con éxito!: {video_path}")
        print(f"   Tamaño: {os.path.getsize(video_path) / (1024*1024):.2f} MB\n")
    else:
        print("❌ Falló la generación de video.\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error en generación de video: {e}\n")
    sys.exit(1)

print("="*50)
print("🎉 ¡MÓDULO 2 FUNCIONA PERFECTAMENTE!")
print("="*50 + "\n")
