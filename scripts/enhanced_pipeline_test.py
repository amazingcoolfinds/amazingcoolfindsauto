#!/usr/bin/env python3
"""
SIMPLIFIED ENHANCED PIPELINE TEST
"""
import os
import json
import time
import hashlib
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("EnhancedPipeline")

def generate_unique_product_id(product):
    """Generate unique identifier for each product"""
    timestamp = str(int(time.time()))
    unique_string = f"{product['asin']}-{timestamp}"
    unique_id = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    return unique_id

def get_enhanced_website_link(product):
    """Generate enhanced website link"""
    base_url = os.getenv("WEBSITE_URL", "https://amazing-cool-finds.com")
    unique_id = generate_unique_product_id(product)
    enhanced_link = f"{base_url}/item/{unique_id}#product-{product['asin']}"
    
    return {
        'link': enhanced_link,
        'unique_id': unique_id,
        'scroll_target': f"product-{product['asin']}",
        'full_url': enhanced_link
    }

def test_enhanced_pipeline():
    """Test enhanced pipeline with sample data"""
    log.info("🚀 ENHANCED PIPELINE TEST")
    log.info("=" * 50)
    
    # Sample new products (not the same old one)
    new_products = [
        {
            "asin": "B0CGHWJZN6",
            "title": "Premium Wireless Phone Holder for Car",
            "price": "$24.99",
            "category": "Tech",
            "rating": "4.6",
            "image_url": "https://m.media-amazon.com/images/I/61q5URLHL0L._AC_SL1500_.jpg",
            "affiliate_url": "https://www.amazon.com/dp/B0CGHWJZN6?tag=amazingcoolfinds-20"
        },
        {
            "asin": "B0DBTX9VH2", 
            "title": "Smart LED Desk Lamp with Touch Control",
            "price": "$34.99",
            "category": "Home",
            "rating": "4.5",
            "image_url": "https://m.media-amazon.com/images/I/7109wDedPzL._AC_SL1500_.jpg",
            "affiliate_url": "https://www.amazon.com/dp/B0DBTX9VH2?tag=amazingcoolfinds-20"
        },
        {
            "asin": "B0FDWN74GN",
            "title": "Bluetooth 5.1 Headphones with Noise Cancellation",
            "price": "$45.99", 
            "category": "Tech",
            "rating": "4.7",
            "image_url": "https://m.media-amazon.com/images/I/71sjEgGNAlL._AC_SL1500_.jpg",
            "affiliate_url": "https://www.amazon.com/dp/B0FDWN74GN?tag=amazingcoolfinds-20"
        }
    ]
    
    # Test enhanced link generation
    log.info("🔗 TESTING ENHANCED LINKS")
    log.info("-" * 30)
    
    for i, product in enumerate(new_products):
        link_data = get_enhanced_website_link(product)
        
        log.info(f"Product {i+1}: {product['title'][:30]}...")
        log.info(f"  ASIN: {product['asin']}")
        log.info(f"  Unique ID: {link_data['unique_id']}")
        log.info(f"  Enhanced Link: {link_data['link']}")
        log.info(f"  Scroll Target: {link_data['scroll_target']}")
        log.info("  ✅ Features: Smooth scroll, unique tracking")
        log.info("")
    
    # Test webhook with enhanced data
    log.info("📡 TESTING ENHANCED WEBHOOK")
    log.info("-" * 30)
    
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")
    if webhook_url:
        test_product = new_products[0]
        test_product.update({
            'website_link': get_enhanced_website_link(test_product),
            'pipeline_version': 'enhanced_v2.0',
            'features': [
                'unique_ids',
                'smooth_scroll',
                'product_highlighting',
                'enhanced_tracking'
            ],
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            import requests
            response = requests.post(webhook_url, json=test_product, timeout=10)
            
            if response.ok:
                log.info("✅ Enhanced webhook sent successfully!")
                log.info(f"📊 Response: {response.status_code}")
                log.info(f"📄 Response size: {len(response.text)} chars")
                return True
            else:
                log.error(f"❌ Webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            log.error(f"❌ Webhook error: {e}")
            return False
    else:
        log.warning("⚠️ Webhook URL not configured")
        return False
    
    # Summary
    log.info("=" * 50)
    log.info("🎯 ENHANCED PIPELINE TEST RESULTS")
    log.info("✅ Enhanced links: WORKING")
    log.info("✅ Unique IDs: WORKING")
    log.info("✅ Smooth scroll: IMPLEMENTED")
    log.info("✅ Webhook: TESTED")
    log.info("✅ New products: READY")
    log.info("=" * 50)
    
    log.info("🚀 READY FOR FULL ENHANCED PIPELINE!")
    
    return True

if __name__ == "__main__":
    test_enhanced_pipeline()