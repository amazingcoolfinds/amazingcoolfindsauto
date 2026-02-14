#!/usr/bin/env python3
"""
Test both fixes: YouTube comment + Make.com webhook
"""
import os
import json
import requests
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FixTest")

def test_make_webhook():
    """Test Make.com webhook with sample product data"""
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")
    
    if not webhook_url:
        log.error("❌ MAKE_WEBHOOK_URL not found")
        return False
    
    # Sample product data (like what gets sent)
    product_data = {
        "asin": "B0FS74F9Q3",
        "title": "FAHREN 2026 Upgraded Android Auto & CarPlay Wireless Adapter",
        "price": "$39.99",
        "category": "Tech",
        "affiliate_url": "https://www.amazon.com/dp/B0FS74F9Q3?tag=amazingcoolfinds-20",
        "video_id": "pxaLqWark2o",
        "video_url": "https://youtube.com/shorts/pxaLqWark2o",
        "timestamp": "2026-02-09T13:00:00Z",
        "voice": "Diana",
        "status": "uploaded"
    }
    
    try:
        log.info("⚡ Testing Make.com webhook...")
        log.info(f"📤 Sending data for ASIN: {product_data['asin']}")
        
        response = requests.post(webhook_url, json=product_data, timeout=10)
        
        if response.ok:
            log.info(f"✅ Webhook sent successfully! Status: {response.status_code}")
            log.info(f"📄 Response: {response.text[:200]}...")
            return True
        else:
            log.error(f"❌ Webhook failed! Status: {response.status_code}")
            log.error(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        log.error(f"❌ Webhook error: {e}")
        return False

def test_youtube_comment_fix():
    """Test YouTube upload with comment posting"""
    log.info("🔧 Testing YouTube comment fix...")
    
    # Since we already have a working token, let's just test the comment posting
    try:
        from youtube_fixed_comment import ProductionYouTubeUploaderFixed
        
        uploader = ProductionYouTubeUploaderFixed()
        video_id = "pxaLqWark2o"  # The video we just uploaded
        affiliate_link = "https://www.amazon.com/dp/B0FS74F9Q3?tag=amazingcoolfinds-20"
        
        success = uploader.post_comment_with_affiliate_link(video_id, affiliate_link)
        
        if success:
            log.info("✅ Comment posting test successful!")
            return True
        else:
            log.warning("⚠️ Comment posting test failed")
            return False
            
    except Exception as e:
        log.error(f"❌ Comment test error: {e}")
        return False

def main():
    """Test both fixes"""
    log.info("🚀 TESTING BOTH FIXES")
    log.info("=" * 50)
    
    # Test 1: Make.com webhook
    log.info("1️⃣ Testing Make.com webhook...")
    webhook_success = test_make_webhook()
    
    # Test 2: YouTube comment fix  
    log.info("\n2️⃣ Testing YouTube comment fix...")
    comment_success = test_youtube_comment_fix()
    
    # Summary
    log.info("\n" + "=" * 50)
    log.info("🎯 FIX TEST RESULTS:")
    log.info(f"   📡 Make.com webhook: {'✅ WORKING' if webhook_success else '❌ FAILED'}")
    log.info(f"   💬 YouTube comment: {'✅ WORKING' if comment_success else '❌ FAILED'}")
    log.info("=" * 50)
    
    if webhook_success and comment_success:
        log.info("🎉 BOTH FIXES WORKING!")
        log.info("🚀 Pipeline is 100% operational!")
    else:
        log.info("⚠️ Some fixes need attention")
    
    return webhook_success and comment_success

if __name__ == "__main__":
    main()