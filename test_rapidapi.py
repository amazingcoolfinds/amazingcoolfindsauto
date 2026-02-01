import requests
import os
from dotenv import load_dotenv

load_dotenv()

url = "https://real-time-amazon-data.p.rapidapi.com/search"

querystring = {"query":"luxury skincare","page":"1","country":"US","sort_by":"RELEVANCE","product_condition":"NEW"}

headers = {
	"x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
	"x-rapidapi-host": os.getenv("RAPIDAPI_HOST")
}

try:
    print(f"🔍 Probando RapidAPI con query: {querystring['query']}...")
    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()
    data = response.json()
    
    if data.get('status') == 'OK' and 'data' in data:
        products = data['data'].get('products', [])
        print(f"✅ ¡ÉXITO! Encontrados {len(products)} productos.")
        for i, p in enumerate(products[:3], 1):
            print(f"{i}. {p.get('product_title')[:60]}...")
            print(f"   Price: {p.get('product_price')}")
            print(f"   ASIN: {p.get('asin')}")
    else:
        print("⚠️ Respuesta inesperada:", data)
except Exception as e:
    print(f"❌ Error en la prueba: {e}")
