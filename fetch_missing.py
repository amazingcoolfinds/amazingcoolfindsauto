from advanced_scraper import AdvancedScraper
import json
import os

s = AdvancedScraper()
d = s.get_details('B0FZ9ZMF3N')
if d:
    # Add meta fields
    d['category'] = 'Tech'
    d['affiliate_url'] = f"https://www.amazon.com/dp/{d['asin']}?tag=amazingcoolfinds-20"
    d['processed_at'] = "2026-02-13T16:00:00"
    d['website_link'] = {
        'link': f"https://amazing-cool-finds.com/item/{d['asin']}#product-{d['asin']}",
        'unique_id': d['asin'],
        'scroll_target': f"product-{d['asin']}",
        'full_url': f"https://amazing-cool-finds.com/item/{d['asin']}#product-{d['asin']}"
    }
    with open('tmp_product.json', 'w') as f:
        json.dump(d, f, indent=2)
    print("DONE")
else:
    print("FAILED")
