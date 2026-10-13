#!/usr/bin/env python3
"""
Prueba del Módulo 1: Extracción de Productos y Generación de Guiones con IA (Groq)
"""
import os
import sys
from pathlib import Path

# Añadir directorios de soporte
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))
sys.path.append(str(BASE_DIR / ".agent" / "skills" / "amazon-scraper" / "scripts"))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

print("\n" + "="*50)
print("🚀 PROBANDO MÓDULO 1: AMAZON + GROQ AI")
print("="*50 + "\n")

# 1. Probar Scraper
print("📦 1. Buscando producto de prueba en Amazon...")
try:
    from amazon_scraper_lib import AmazonScraper
    tag = os.getenv("AMAZON_ASSOCIATE_TAG", "amazingcoolfinds-20")
    scraper = AmazonScraper(associate_tag=tag)

    # Buscar producto
    products = scraper.search("smart home gadgets 2026", max_results=1)
    if not products:
        print("❌ No se encontraron productos.")
        sys.exit(1)

    product = products[0]
    print(f"✅ Producto encontrado:")
    print(f"   - Título: {product.get('title')}")
    print(f"   - ASIN: {product.get('asin')}")
    print(f"   - Precio: {product.get('price')}")
    print(f"   - Enlace Afiliado: {product.get('affiliate_url')}\n")
except Exception as e:
    print(f"❌ Error en extracción de Amazon: {e}\n")
    sys.exit(1)

# 2. Probar IA (Groq)
print("🧠 2. Generando guión viral con Groq AI...")
try:
    from groq_generators import GroqScriptGenerator
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ Falta GROQ_API_KEY en .env")
        sys.exit(1)

    ai_gen = GroqScriptGenerator(api_key=groq_key)
    script = ai_gen.generate_script(product)

    if script:
        print("✅ Guión generado con éxito:")
        print(f"   - Título sugerido: {script.get('title')}")
        print(f"   - Narración (Audio): \"{script.get('narration')}\"")
        print(f"   - Hashtags: {' '.join(script.get('hashtags', []))}\n")
    else:
        print("❌ Groq no pudo generar el guión.")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error en Groq AI: {e}\n")
    sys.exit(1)

print("="*50)
print("🎉 ¡MÓDULO 1 FUNCIONA PERFECTAMENTE!")
print("="*50 + "\n")
