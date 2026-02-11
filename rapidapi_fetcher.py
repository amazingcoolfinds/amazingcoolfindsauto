#!/usr/bin/env python3
import requests
import os
import logging
from typing import List, Dict

log = logging.getLogger("RapidAPIFetcher")

class AmazonRapidAPI:
    """
    Fetcher for Amazon products using RapidAPI (HolyEntGold Amazon Data Scraper).
    Provides high-quality details and images via product enrichment.
    """
    
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.api_host = os.getenv("RAPIDAPI_HOST")
        self.associate_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "liveitupdea09-20")
        
        # New API endpoint for product details
        self.base_url = f"https://{self.api_host}"
        
        if not self.api_key or not self.api_host:
            log.warning("RapidAPI credentials missing in .env")

    def get_product_details(self, asin: str) -> Dict:
        """
        Fetch detailed product data including high-res images using HolyEntGold API
        """
        if not self.api_key:
            return None
            
        try:
            url = f"{self.base_url}/products/{asin}"
            headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": self.api_host
            }

            log.info(f"Enriching product {asin} via RapidAPI...")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            # Adjust based on API structure (sometimes 'data' is wrapper)
            product_data = data.get('data', data)
            
            # Extract key details
            title = product_data.get('product_title')
            price = product_data.get('product_price')
            rating = product_data.get('product_star_rating')
            
            # Get up to 7 images for dynamic carousel
            # HolyEntGold returns 'product_photos' as list of URLs
            images = product_data.get('product_photos', [])
            if not images:
                single_img = product_data.get('product_photo')
                if single_img:
                    images = [single_img]
            
            images = [img for img in images if img][:7]
            
            # Get bullet points
            bullets = product_data.get('product_attributes', [])
            if isinstance(bullets, str): # Handle if it returns a string block
                bullets = [bullets]
            
            if title and images:
                return {
                    "asin": asin,
                    "title": title,
                    "price": price,
                    "rating": str(rating),
                    "image_url": images[0],
                    "images": images,
                    "bullets": bullets,
                    "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}"
                }
            
            log.warning(f"RapidAPI returned incomplete data for {asin}")
            return None
            
        except Exception as e:
            log.warning(f"RapidAPI enrichment failed for {asin}: {e}")
            return None

    def search(self, keywords: str, count: int = 3) -> List[Dict]:
        """
        NOTE: This specific API actor (HolyEntGold) appears to be for product details, not search.
        We will return empty list here to force fallback to the scraper for discovery,
        which will then call get_product_details() to get images.
        """
        log.info(f"Skipping RapidAPI search (using scraper for discovery, RapidAPI for details)")
        return []
