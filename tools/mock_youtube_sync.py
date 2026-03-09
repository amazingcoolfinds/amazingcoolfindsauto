import json
import os
from pathlib import Path
from datetime import datetime

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTS_JSON = BASE_DIR / "amazing" / "data" / "products.json"

def mock_youtube_data():
    if not PRODUCTS_JSON.exists():
        print(f"Error: {PRODUCTS_JSON} not found.")
        return

    with open(PRODUCTS_JSON, 'r') as f:
        products = json.load(f)

    if not products:
        print("Error: No products in products.json")
        return

    # Mark at least 2 products as YouTube uploaded
    # We'll pick the first 2 and give them different dates to test sorting
    for i, p in enumerate(products[:2]):
        p['youtube_uploaded'] = True
        p['youtube_video_id'] = f"mock_vid_{i}"
        p['youtube_url'] = f"https://www.youtube.com/watch?v=mock_vid_{i}"
        # Set one older than the other
        if i == 0:
            p['processed_at'] = "2026-03-01T10:00:00"
        else:
            p['processed_at'] = "2026-03-05T10:00:00"
        print(f"Mocked product {p['asin']} as YouTube uploaded.")

    # Mark one non-youtube product as very new to test it doesn't jump ahead of youtube ones
    if len(products) > 2:
        products[2]['youtube_uploaded'] = False
        products[2]['processed_at'] = datetime.now().isoformat()
        print(f"Mocked product {products[2]['asin']} as very new but NOT YouTube uploaded.")

    with open(PRODUCTS_JSON, 'w') as f:
        json.dump(products, f, indent=2)
    print("Mocks applied to products.json.")

if __name__ == "__main__":
    mock_youtube_data()
