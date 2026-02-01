#!/usr/bin/env python3
import logging
from youtube_uploader import YouTubeUploader

def test_auth():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Iniciando sistema de autorización de YouTube...")
    print("📢 Atento: Se abrirá una pestaña en tu navegador para que elijas tu cuenta de Google.")
    
    try:
        uploader = YouTubeUploader()
        print("✅ ¡Autorización exitosa! El archivo 'token.json' se ha creado.")
    except Exception as e:
        print(f"❌ Error durante la autorización: {e}")

if __name__ == "__main__":
    test_auth()
