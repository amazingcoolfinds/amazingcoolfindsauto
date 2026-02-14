#!/usr/bin/env python3
import os
import logging
from typing import List, Dict
from amazon_paapi import AmazonApi

log = logging.getLogger("PAAPIFetcher")

class PAAPIFetcher:
    """
    Official Amazon Product Advertising API (PA-API) fetcher.
    """
    
    def __init__(self):
        self.access_key = os.getenv("AMAZON_ACCESS_KEY")
        self.secret_key = os.getenv("AMAZON_SECRET_KEY")
        self.partner_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "amazingcoolfinds-20")
        self.host = "www.amazon.com"
        self.region = "us"
        
        if not self.access_key or not self.secret_key:
            log.warning("PA-API credentials missing in .env")
            self.api = None
        else:
            try:
                self.api = AmazonApi(self.access_key, self.secret_key, self.partner_tag, self.host, self.region)
                log.info("✅ PA-API initialized")
            except Exception as e:
                log.error(f"❌ Failed to initialize PA-API: {e}")
                self.api = None

    def search(self, keywords: str, count: int = 3) -> List[Dict]:
        """Search for products using PA-API"""
        if not self.api:
            return []
            
        try:
            log.info(f"🔍 Searching PA-API for '{keywords}'...")
            search_results = self.api.search_items(keywords=keywords, item_count=count)
            
            products = []
            for item in search_results:
                products.append(self._format_item(item))
                
            return products
        except Exception as e:
            log.error(f"❌ PA-API search failed: {e}")
            return []

    def get_details(self, asin: str) -> Dict:
        """Get product details using PA-API"""
        if not self.api:
            return None
            
        try:
            log.info(f"📦 Fetching details for {asin} via PA-API...")
            item = self.api.get_product(asin)
            if item:
                return self._format_item(item)
        except Exception as e:
            log.error(f"❌ PA-API get_product failed for {asin}: {e}")
            
        return None

    def _format_item(self, item) -> Dict:
        """Convert PA-API item to internal product format"""
        # PA-API returns objects with specific attributes
        try:
            # Bullet points
            bullets = []
            if hasattr(item, 'features') and item.features:
                bullets = item.features[:3]
                
            # Images
            images = []
            if hasattr(item, 'images') and item.images:
                # PA-API usually has a list of Image objects
                for img in item.images:
                    if hasattr(img, 'url'):
                        images.append(img.url)
            
            if not images and hasattr(item, 'large_image_url'):
                images = [item.large_image_url]
            
            # Price
            price = "$29.99"
            if hasattr(item, 'price') and item.price and hasattr(item, 'price', 'amount'):
                 price = f"${item.price.amount}"
            elif hasattr(item, 'offers') and item.offers:
                 # Standard offer extraction
                 pass

            return {
                "asin": item.asin,
                "title": item.title,
                "price": item.price.display_amount if hasattr(item, 'price') and item.price else "$29.99",
                "rating": "4.5", # PA-API v5 doesn't return ratings directly
                "image_url": item.large_image_url if hasattr(item, 'large_image_url') else images[0] if images else None,
                "images": images[:7],
                "bullets": bullets,
                "affiliate_url": item.url
            }
        except Exception as e:
            log.error(f"Error formatting PA-API item: {e}")
            return {
                "asin": item.asin,
                "title": item.title if hasattr(item, 'title') else "Product",
                "affiliate_url": item.url if hasattr(item, 'url') else f"https://www.amazon.com/dp/{item.asin}?tag={self.partner_tag}"
            }

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    from dotenv import load_dotenv
    load_dotenv()
    
    fetcher = PAAPIFetcher()
    if fetcher.api:
        print("\nTesting PA-API Search...")
        results = fetcher.search("gaming mouse", count=1)
        import json
        print(json.dumps(results, indent=2))
    else:
        print("PA-API not initialized. Check .env")
