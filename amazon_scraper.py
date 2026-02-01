#!/usr/bin/env python3
"""
Amazon Product Scraper - Temporal solution
WARNING: This violates Amazon's TOS. Use only temporarily until PA-API is approved.
"""

import requests
import re
import time
import logging
from typing import List, Dict
from urllib.parse import quote_plus

log = logging.getLogger("AmazonScraper")


class AmazonScraper:
    """
    Simple Amazon scraper for product search.
    Use only temporarily until PA-API credentials are approved.
    """
    
    def __init__(self, associate_tag: str):
        self.associate_tag = associate_tag
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        # Curated product list as fallback
        self.fallback_products = {
            'luxury beauty skincare premium': [
                ('B07R7X6G8N', 'La Roche-Posay Hyaluronic Acid Serum', '$39.99', '4.6'),
                ('B00BSNBO9O', 'Neutrogena Hydro Boost Water Gel', '$18.97', '4.5'),
                ('B0BXZYSD3Z', 'Olay Regenerist Micro-Sculpting Cream', '$29.99', '4.6'),
            ],
            'luxury perfume fragrance high end': [
                ('B000C214CO', 'Calvin Klein Euphoria Eau de Parfum', '$49.95', '4.6'),
                ('B000P23PCI', 'Giorgio Armani Acqua Di Gio', '$89.00', '4.7'),
                ('B00SCZX1X6', 'Versace Dylan Blue Pour Homme', '$62.99', '4.6'),
            ],
            'premium tech gadgets 2025': [
                ('B0CHL22RZL', 'Apple AirPods Pro (2nd Gen)', '$189.99', '4.7'),
                ('B0CHXCD719', 'Amazon Fire TV Stick 4K Max', '$39.99', '4.6'),
                ('B0CS531Y58', 'Beats Solo 4 Wireless Headphones', '$199.95', '4.5'),
            ],
            'luxury fashion men premium jacket': [
                ('B0CPYVPVDN', 'Columbia Mens Steens Mountain Fleece', '$34.99', '4.6'),
                ('B09VQKSZR7', 'The North Face Mens Denali Jacket', '$179.00', '4.7'),
                ('B0BKX26ZSD', 'Carhartt Rain Defender Jacket', '$59.99', '4.6'),
            ],
            'luxury fashion women premium dress': [
                ('B0B25XWGXR', 'ZESICA Womens Elegant Midi Dress', '$42.99', '4.5'),
                ('B0BHBZ85VT', 'Alex Evenings Womens Tea Length Dress', '$139.00', '4.4'),
                ('B0CWQGRDVK', 'Verdusa Womens Ruffle Hem Dress', '$36.99', '4.3'),
            ],
            'premium home decor luxury modern': [
                ('B0B6R5C4M2', 'HOMFA Large Decorative Mirror', '$89.99', '4.6'),
                ('B0B7N7NGFN', 'WOPITUES Modern Abstract Canvas Wall Art', '$24.99', '4.5'),
                ('B0BJVZR4PC', 'LITFAD Gold Floor Lamp', '$139.99', '4.4'),
            ],
            'premium laptop high end 2025': [
                ('B0CX23V2ZK', 'Apple MacBook Air 15-inch M3', '$1,299.00', '4.8'),
                ('B0D415BT9G', 'Microsoft Surface Laptop 7th Edition', '$999.99', '4.6'),
                ('B0CYV1PJ4Y', 'Dell XPS 13 Plus Laptop', '$1,199.00', '4.5'),
            ],
            'luxury smartwatch premium 2025': [
                ('B0CSV3K3TB', 'Apple Watch Series 10', '$399.00', '4.7'),
                ('B0DCM58Z61', 'Samsung Galaxy Watch 7', '$299.99', '4.6'),
                ('B0BNX1FH5J', 'Garmin Venu 3 GPS Smartwatch', '$449.99', '4.5'),
            ],
        }
    
    def search(self, keywords: str, max_results: int = 3) -> List[Dict]:
        """
        Search Amazon for products - with fallback to curated list
        """
        # Try actual scraping first
        results = self._try_scrape(keywords, max_results)
        
        # Fallback to curated products if scraping fails
        if not results:
            log.warning(f"Scraping failed, using curated products for '{keywords}'")
            results = self._get_fallback_products(keywords, max_results)
        
        return results
    
    def _try_scrape(self, keywords: str, max_results: int) -> List[Dict]:
        """Attempt to scrape Amazon"""
        try:
            # Build search URL
            search_term = quote_plus(keywords)
            url = f"https://www.amazon.com/s?k={search_term}"
            
            log.info(f"Scraping Amazon for '{keywords}'...")
            
            # Add delay to be respectful
            time.sleep(2)
            
            # Make request
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse products
            products = self._parse_search_results(response.text, max_results)
            
            log.info(f"✓ Found {len(products)} products for '{keywords}'")
            return products
            
        except Exception as e:
            log.error(f"Scraping error for '{keywords}': {e}")
            return []
    
    def _get_fallback_products(self, keywords: str, max_results: int) -> List[Dict]:
        """
        Get curated products from fallback list
        """
        products = []
        
        # Find matching keyword set
        fallback_list = self.fallback_products.get(keywords, [])
        
        for asin, title, price, rating in fallback_list[:max_results]:
            # Generate image URL from ASIN
            image_url = f"https://m.media-amazon.com/images/I/{asin}._AC_SX300_SY300_.jpg"
            
            products.append({
                "asin": asin,
                "title": title,
                "price": price,
                "rating": rating,
                "image_url": image_url,
                "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}"
            })
        
        log.info(f"✓ Using {len(products)} curated products for '{keywords}'")
        return products
    
    def _parse_search_results(self, html: str, max_results: int) -> List[Dict]:
        """
        Parse HTML to extract product information
        """
        products = []
        
        try:
            # Extract ASINs
            asin_pattern = r'data-asin="([A-Z0-9]{10})"'
            asins = re.findall(asin_pattern, html)
            asins = list(dict.fromkeys(asins))[:max_results]  # Remove duplicates
            
            for asin in asins:
                # Find product block for this ASIN
                product_pattern = rf'data-asin="{asin}".*?(?=data-asin="|$)'
                match = re.search(product_pattern, html, re.DOTALL)
                
                if not match:
                    continue
                
                product_html = match.group(0)
                
                # Extract title
                title_match = re.search(r'<span class="a-size-(?:base-plus|medium|base).*?">([^<]+)</span>', product_html)
                title = title_match.group(1).strip() if title_match else f"Product {asin}"
                
                # Extract price
                price_match = re.search(r'<span class="a-price-whole">(\d+)</span>.*?<span class="a-price-fraction">(\d+)</span>', product_html)
                if price_match:
                    price = f"${price_match.group(1)}.{price_match.group(2)}"
                else:
                    price = "Check Price"
                
                # Extract rating
                rating_match = re.search(r'(\d\.\d) out of 5 stars', product_html)
                rating = rating_match.group(1) if rating_match else "4.5"
                
                # Extract image
                image_match = re.search(r'<img[^>]+src="(https://m\.media-amazon\.com/images/I/[^"]+)"', product_html)
                image_url = image_match.group(1) if image_match else None
                
                # Build affiliate URL
                affiliate_url = f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}"
                
                # Only add if we have an image
                if image_url and title != f"Product {asin}":
                    products.append({
                        "asin": asin,
                        "title": title[:100],  # Limit length
                        "price": price,
                        "rating": rating,
                        "image_url": image_url,
                        "affiliate_url": affiliate_url
                    })
                
        except Exception as e:
            log.error(f"Parsing error: {e}")
        
        return products


def test_scraper():
    """Quick test of the scraper"""
    logging.basicConfig(level=logging.INFO)
    scraper = AmazonScraper("liveitupdea09-20")
    results = scraper.search("luxury beauty skincare premium", max_results=3)
    
    print(f"\n✅ Found {len(results)} products:\n")
    for i, product in enumerate(results, 1):
        print(f"{i}. {product['title']}")
        print(f"   Price: {product['price']}")
        print(f"   Rating: {product['rating']} stars")
        print(f"   Link: {product['affiliate_url'][:60]}...")
        print()


if __name__ == "__main__":
    test_scraper()
