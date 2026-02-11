#!/usr/bin/env python3
import sys
import json
import os

# Add current directory to path so we can import the library
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from amazon_scraper_lib import AmazonScraper

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python scrape.py <ASIN_OR_URL>"}))
        sys.exit(1)
        
    query = sys.argv[1]
    
    # Initialize scraper
    associate_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "amazingcoolfinds-20")
    scraper = AmazonScraper(associate_tag)
    
    try:
        if "amazon.com" in query:
             import re
             asin_match = re.search(r'/([A-Z0-9]{10})', query)
             if asin_match:
                 asin = asin_match.group(1)
             else:
                 # Try to parse query as ASIN directly if it looks like one
                 if re.match(r'^[A-Z0-9]{10}$', query):
                    asin = query
                 else:
                    print(json.dumps({"error": "Invalid Amazon URL or ASIN"}))
                    sys.exit(1)
        else:
            # Assume ASIN
            asin = query
            
        # Get details using the new method
        product = scraper.get_details(asin)
        
        if product:
            print(json.dumps(product, indent=2))
        else:
            print(json.dumps({"error": "Product not found or scraping blocked"}))
            
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
