import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# We need the product details endpoint for images and descriptions usually
# Or check if search provides them.
url = "https://real-time-amazon-data.p.rapidapi.com/product-details"

# Let's test with a specific ASIN from the previous results: B0B2RM68G2
querystring = {"asin":"B0B2RM68G2","country":"US"}

headers = {
	"x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
	"x-rapidapi-host": os.getenv("RAPIDAPI_HOST")
}

try:
    print(f"🔍 Fetching details for ASIN: {querystring['asin']}...")
    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()
    data = response.json()
    
    # Save to file to inspect
    with open('product_details_debug.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    if data.get('status') == 'OK' and 'data' in data:
        prod = data['data']
        print(f"✅ Title: {prod.get('product_title')}")
        print(f"✅ Images count: {len(prod.get('product_photos', []))}")
        print(f"✅ Bullet points: {len(prod.get('about_product', []))}")
    else:
        print("⚠️ Unexpected response structure.")
except Exception as e:
    print(f"❌ Error: {e}")
