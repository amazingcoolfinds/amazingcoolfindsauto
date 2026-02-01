#!/usr/bin/env python3
"""
Test de Product Advertising API 5.0
"""
from amazon_paapi import AmazonApi

# Credenciales PA-API 5.0
ACCESS_KEY = "AKPA4S69KN1769900663"
SECRET_KEY = "JNG2VS8B+7oiCRDn8Pn8VlXC4lC1IOspMnF6aH+v"
ASSOCIATE_TAG = "liveitupdea09-20"

try:
    print("🔧 Configurando API...")
    api = AmazonApi(
        key=ACCESS_KEY,
        secret=SECRET_KEY,
        tag=ASSOCIATE_TAG,
        country="US"
    )
    
    print("🔍 Buscando productos de lujo...")
    results = api.search_items(keywords="luxury skincare")
    
    if results and hasattr(results, 'items') and results.items:
        print(f"\n✅ ¡FUNCIONA! Encontrados {len(results.items)} productos:\n")
        for i, item in enumerate(results.items[:5], 1):
            title = item.item_info.title.display_value if item.item_info and item.item_info.title else "Sin título"
            print(f"{i}. {title[:60]}...")
        print("\n✅ Las credenciales de PA-API 5.0 son válidas!")
    else:
        print("⚠️  La API respondió pero sin productos")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPosibles causas:")
    print("  - Credenciales incorrectas")
    print("  - Cuenta no aprobada para PA-API")
    print("  - Límite de requests excedido")
