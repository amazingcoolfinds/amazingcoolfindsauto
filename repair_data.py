#!/usr/bin/env python3
import json
import logging
from pipeline_scraper import AmazonFetcher

logging.basicConfig(level=logging.INFO)

def repair():
    print("🛠️ Reparando datos del producto Armani...")
    amazon = AmazonFetcher()
    
    # Fetch fresh details for the specific ASIN to ensure 100% match
    target_asin = "B00BYIMWYE"
    # Access inner rapidapi instance
    details = amazon.rapidapi._get_details(target_asin)
    
    if not details:
        print("❌ No se pudieron obtener detalles de la API. Usando backup manual.")
        return

    # Construct clean product object
    product = {
        "asin": target_asin,
        "title": details.get('product_title', "A|X Armani Exchange Men's Watch"),
        "price": details.get('product_price', "$128.95"),
        "rating": str(details.get('product_star_rating', "4.6")),
        "image_url": details.get('product_photo'),
        "images": details.get('product_photos', [])[:5], # Ensure we get list
        "affiliate_url": f"https://www.amazon.com/dp/{target_asin}?tag=liveitupdea09-20",
        "youtube_url": "https://youtu.be/ebXqDHJydBE", # Preserve the uploaded video URL
        "category": "Clothing",
        "commission": "4%" # Kept in data, hidden in UI
    }
    
    # Save
    with open("data/products.json", "w", encoding='utf-8') as f:
        json.dump([product], f, indent=2, ensure_ascii=False)
        
    print(f"✅ Reparación completa. Imágenes encontradas: {len(product['images'])}")
    print("El producto en la web ahora debería coincidir exactamente.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    repair()
