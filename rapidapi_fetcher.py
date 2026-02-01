#!/usr/bin/env python3
import requests
import os
import logging
from typing import List, Dict

log = logging.getLogger("RapidAPIFetcher")

class AmazonRapidAPI:
    """
    Fetcher for Amazon products using RapidAPI (Real-Time Amazon Data).
    Provides high-quality, real-time data.
    """
    
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.api_host = os.getenv("RAPIDAPI_HOST")
        self.associate_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "liveitupdea09-20")
        self.url = f"https://{self.api_host}/search"
        
        if not self.api_key or not self.api_host:
            log.warning("RapidAPI credentials missing in .env")

    def search(self, keywords: str, count: int = 3) -> List[Dict]:
        """
        Search for products using RapidAPI
        """
        if not self.api_key:
            return []
            
        try:
            querystring = {
                "query": keywords,
                "page": "1",
                "country": "US",
                "sort_by": "RELEVANCE",
                "product_condition": "NEW"
            }

            headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": self.api_host
            }

            log.info(f"Fetching from RapidAPI for '{keywords}'...")
            response = requests.get(self.url, headers=headers, params=querystring, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') != 'OK' or 'data' not in data:
                log.error(f"RapidAPI returned error: {data.get('message', 'Unknown error')}")
                return []
                
            raw_products = data['data'].get('products', [])
            products = []
            
            for p in raw_products[:count]:
                asin = p.get('asin')
                log.info(f"  Fetching details for {asin}...")
                
                # Fetch detailed info for each product (images and bullet points)
                details = self._get_details(asin)
                
                title = details.get('product_title', p.get('product_title'))
                price = details.get('product_price', p.get('product_price', 'Check Price'))
                rating = details.get('product_star_rating', p.get('product_star_rating', '4.5'))
                
                # Get up to 5 images
                images = details.get('product_photos', [p.get('product_photo')])[:5]
                # Get bullet points for script generation
                bullets = details.get('about_product', [])
                
                affiliate_url = f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}"
                
                if asin and title and images:
                    products.append({
                        "asin": asin,
                        "title": title,
                        "price": price,
                        "rating": str(rating),
                        "image_url": images[0], # Primary image
                        "images": images,        # All images for carousel
                        "bullets": bullets,      # For better scripts
                        "affiliate_url": affiliate_url
                    })
            
            log.info(f"✓ RapidAPI returned {len(products)} enriched products")
            return products
            
        except Exception as e:
            log.error(f"RapidAPI search failed: {e}")
            return []

    def _get_details(self, asin: str) -> Dict:
        """Fetch full product details"""
        try:
            url = f"https://{self.api_host}/product-details"
            querystring = {"asin": asin, "country": "US"}
            headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": self.api_host
            }
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            if response.status_code == 200:
                res = response.json()
                return res.get('data', {})
            return {}
        except Exception as e:
            log.error(f"Failed to fetch details for {asin}: {e}")
            return {}
