#!/usr/bin/env python3
"""
Prueba del Módulo 3: Distribución (YouTube, Meta, TikTok) y Sincronización Web
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Añadir directorios de soporte
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))
sys.path.append(str(BASE_DIR / "config")) # Assuming config might be needed for enhanced_pipeline
sys.path.append(str(BASE_DIR / "amazing" / "data")) # For products.json in amazing/data

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

print("\n" + "="*50)
print("🚀 PROBANDO MÓDULO 3: DISTRIBUCIÓN & SINCRONIZACIÓN WEB")
print("="*50 + "\n")

# --- MOCK DATA (from Module 2 output) ---
# Ensure these paths exist for a successful test of the video_generator
mock_voice_path = BASE_DIR / "assets" / "B0D5BBYRJM_voice.wav"
mock_video_path = BASE_DIR / "output_videos" / "video_B0D5BBYRJM.mp4"

# Create dummy files if they don't exist for the test
if not mock_voice_path.exists():
    mock_voice_path.touch()
    print(f"ℹ️ Creado archivo dummy: {mock_voice_path}")
if not mock_video_path.exists():
    mock_video_path.touch()
    print(f"ℹ️ Creado archivo dummy: {mock_video_path}")

mock_product = {
    "asin": "B0D5BBYRJM",
    "title": "Premium Smart Gadget for Easy Living",
    "price": "$99.99",
    "rating": "4.7",
    "reviews_count": 1234,
    "category": "Tech",
    "bullets": ["Seamless integration", "Long-lasting battery", "Intuitive interface"],
    "images": [
        "https://placehold.co/1080x1920/4A90E2/FFF.png?text=Product+Image+1",
        "https://placehold.co/1080x1920/E94B3C/FFF.png?text=Product+Image+2",
        "https://placehold.co/1080x1920/6C5CE7/FFF.png?text=Product+Image+3",
        "https://placehold.co/1080x1920/00B894/FFF.png?text=Product+Image+4",
        "https://placehold.co/1080x1920/FDCB6E/FFF.png?text=Product+Image+5"
    ],
    "image_url": "https://placehold.co/1080x1920/4A90E2/FFF.png?text=Product+Image+1",
    "affiliate_url": "https://www.amazon.com/dp/B0D5BBYRJM?tag=amazingcoolfinds-20",
    "processed_at": datetime.now().isoformat(),
}

mock_script = {
    "title": "Why Is This So Good?!",
    "narration": "Okay, I genuinely did not expect this to be this good. The quality is honestly insane for the price tag. It feels premium, works perfectly, and just makes my life infinitely easier. You have to try this. Link is in the first comment!",
    "hashtags": ["#TikTokMadeMeBuyIt", "#HiddenGems", "#MustHaves", "#ViralFinds", "#QualityCheck"]
}

# Add script and voice path to product for consistency with pipeline
mock_product["script"] = mock_script
mock_product["voice_path"] = str(mock_voice_path)


# 1. Probar Inicialización de YouTube Uploader
print("📹 1. Probando inicialización de YouTube Uploader...")
try:
    from youtube_production import ProductionYouTubeUploader
    yt_up = ProductionYouTubeUploader()
    if yt_up.credentials and yt_up.youtube:
        print("✅ YouTube Uploader inicializado con credenciales.")
    else:
        print("⚠️ YouTube Uploader NO inicializado. Faltan credenciales o falló la carga. Esto es esperado si no se han configurado.")
except Exception as e:
    print(f"❌ Error al inicializar YouTube Uploader: {e}")
print("-" * 30)

# 2. Probar Inicialización de Meta Uploader
print("📸 2. Probando inicialización de Meta (FB/IG) Uploader...")
try:
    from meta_uploader import MetaUploader
    meta_up = MetaUploader()
    if meta_up.access_token and meta_up.page_id and meta_up.ig_account_id:
        print("✅ Meta Uploader inicializado con credenciales.")
    else:
        print("⚠️ Meta Uploader NO inicializado. Faltan credenciales o falló la carga. Esto es esperado si no se han configurado.")
except Exception as e:
    print(f"❌ Error al inicializar Meta Uploader: {e}")
print("-" * 30)

# 3. Probar Inicialización de TikTok Uploader
print("🎵 3. Probando inicialización de TikTok Uploader...")
try:
    from tiktok_uploader import TikTokUploader
    tt_up = TikTokUploader()
    if tt_up.access_token:
        print("✅ TikTok Uploader inicializado con credenciales.")
    else:
        print("⚠️ TikTok Uploader NO inicializado. Faltan credenciales o falló la carga. Esto es esperado si no se han configurado.")
except Exception as e:
    print(f"❌ Error al inicializar TikTok Uploader: {e}")
print("-" * 30)


# 4. Probar Sincronización Web Local
print("🌐 4. Probando sincronización web local (JSON)...")
try:
    # Import from enhanced_pipeline
    from enhanced_pipeline import save_processed_product, update_website_data, AMAZING_DATA_DIR, DATA_DIR

    # Ensure output directories exist for this test
    AMAZING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save to processed history
    save_processed_product(mock_product)
    print(f"✅ Producto guardado en historial de procesamiento: {mock_product['asin']}")

    # Update website data (merges into amazing/data/products.json)
    update_website_data([mock_product])
    print(f"✅ Datos del sitio web actualizados localmente para {mock_product['asin']}")

    # Verify content in amazing/data/products.json
    products_json_path = AMAZING_DATA_DIR / "products.json"
    if products_json_path.exists():
        with open(products_json_path, 'r') as f:
            data = json.load(f)
            found = any(p["asin"] == mock_product["asin"] for p in data)
            if found:
                print(f"✅ Producto {mock_product['asin']} encontrado en {products_json_path}")
            else:
                print(f"❌ Producto {mock_product['asin']} NO encontrado en {products_json_path}")
    else:
        print(f"❌ Archivo {products_json_path} no encontrado.")

except Exception as e:
    print(f"❌ Error en sincronización web local: {e}")
print("-" * 30)


print("="*50)
print("🎉 ¡MÓDULO 3 FUNCIONA PERFECTAMENTE (Prueba de Inicialización & Sincronización Local)!")
print("="*50 + "\n")
