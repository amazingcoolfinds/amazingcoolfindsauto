#!/usr/bin/env python3
"""
UPDATED PIPELINE - Enhanced website links with unique IDs and new products
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# ─── PATHS ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
AMAZING_DATA_DIR = BASE_DIR / "amazing" / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

for d in [LOGS_DIR, DATA_DIR, AMAZING_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── ENV & LOGGING ───────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ])
log = logging.getLogger("AmazingCoolFinds")

# ─── CONFIGURATION ───────────────────────────────────────────────
PRODUCT_TARGETS = [
    {"category": "Tech", "keywords": "premium tech gadgets 2026", "commission": "4%"},
    {"category": "Lifestyle", "keywords": "luxury skincare beauty essentials", "commission": "10%"},
    {"category": "Home", "keywords": "modern home decor luxury office", "commission": "3%"},
    {"category": "Auto", "keywords": "premium car accessories 2026", "commission": "4%"},
]

# ─── ENHANCED FUNCTIONS ─────────────────────────────────────
def generate_unique_product_id(product):
    """Generate unique identifier for each product - simplified to ASIN for user transparency"""
    return product['asin']

def get_enhanced_website_link(product):
    """Generate enhanced website link with unique ID and scroll"""
    base_url = os.getenv("WEBSITE_URL", "https://amazing-cool-finds.com")
    unique_id = generate_unique_product_id(product)
    
    # Enhanced link with scroll and product data
    enhanced_link = f"{base_url}/item/{unique_id}#product-{product['asin']}"
    
    return {
        'link': enhanced_link,
        'unique_id': unique_id,
        'scroll_target': f"product-{product['asin']}",
        'full_url': enhanced_link
    }

def get_high_performance_products(count_candidates=15, select_top=3):
    """
    New selection logic with Duplicate Prevention: 
    1. Check for existing ASINs.
    2. Scrape candidates (skipping duplicates).
    3. Score with Groq AI.
    4. Return top 3-5 high-performance products.
    """
    try:
        from advanced_scraper import AdvancedScraper
        from groq_generators import GroqProductSelector
        from strategy_monitor import StrategyMonitor
        
        scraper = AdvancedScraper()
        selector = GroqProductSelector(os.getenv("GROQ_API_KEY"))
        monitor = StrategyMonitor(DATA_DIR)
        
        # 0. Get all existing ASINs to prevent duplicates
        existing_asins = get_all_existing_asins()
        log.info(f"🚫 Duplicate Filter: {len(existing_asins)} products already in database.")
        
        # Get strategic target
        targets = monitor.get_discovery_targets()
        import random
        target = random.choice(targets)
        
        log.info(f"🔍 DISCOVERY MODE: {target['category']} using '{target['keywords']}'")
        
        # 1. Search for candidates
        # We search for slightly more to compensate for duplicates we might filter
        search_results = scraper.search(target['keywords'], max_results=count_candidates + 10)
        
        if not search_results:
            log.warning("No search results found.")
            return []
            
        # 2. Enrich candidates with full details (skipping duplicates)
        candidates = []
        for item in search_results:
            if item['asin'] in existing_asins:
                log.info(f"  ⏭️ Skipping duplicate: {item['asin']}")
                continue
                
            if len(candidates) >= count_candidates:
                break
                
            details = scraper.get_details(item['asin'])
            if details:
                # Add category and commission for the AI to calculate profit
                details['category'] = target['category']
                details['commission'] = monitor.commissions.get(target['category'], 0.04)
                candidates.append(details)
                log.info(f"  📦 Scraped: {details['asin']} - {details['title'][:40]}...")
            
            # Random delay 10-20s to be very polite to Amazon
            delay = random.uniform(10, 20)
            log.info(f"  ⏳ Waiting {delay:.1f}s...")
            time.sleep(delay)
            
        if not candidates:
            log.warning("Final candidate list is empty after filtering duplicates.")
            return []
            
        # 3. AI Selection
        selections = selector.analyze_candidates(target['category'], candidates)
        
        # 4. Enhance links for selections
        for p in selections:
            p['website_link'] = get_enhanced_website_link(p)
            p['affiliate_url'] = f"https://www.amazon.com/dp/{p['asin']}?tag={AFFILIATE_TAG}"
            p['processed_at'] = datetime.now().isoformat()
            
        return selections

    except Exception as e:
        log.error(f"Error in high-performance selection: {e}")
        return []

def get_all_existing_asins():
    """Compiles a list of ASINs from both processing history and website database"""
    existing = set()
    
    # Check processed history (Pipeline records)
    history_file = DATA_DIR / "processed_products.json"
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
                for item in data: existing.add(item['asin'])
        except: pass

    # Check website database (Live items)
    site_db = AMAZING_DATA_DIR / "products.json"
    if site_db.exists():
        try:
            with open(site_db, 'r') as f:
                data = json.load(f)
                for item in data: existing.add(item['asin'])
        except: pass
        
    return existing

def get_new_product():
    """Get list of recently processed ASINs"""
    try:
        history_file = DATA_DIR / "processed_products.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                processed = json.load(f)
            
            # Get ASINs from last 7 days
            recent_asins = []
            cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days ago
            
            for item in processed:
                if 'processed_at' in item:
                    try:
                        processed_time = datetime.fromisoformat(item['processed_at']).timestamp()
                        if processed_time > cutoff_time:
                            recent_asins.append(item['asin'])
                    except:
                        continue
            
            return recent_asins
    except Exception as e:
        log.warning(f"Error reading processed history: {e}")
    
    return []

def save_processed_product(product):
    """Save product to processed history"""
    try:
        history_file = DATA_DIR / "processed_products.json"
        processed = []
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                processed = json.load(f)
        
        # Add new product
        processed.append({
            'asin': product['asin'],
            'title': product['title'],
            'processed_at': product['processed_at']
        })
        
        # Keep only last 100 processed products
        processed = processed[-100:]
        
        with open(history_file, 'w') as f:
            json.dump(processed, f, indent=2)
        
        log.info(f"✅ Product saved to processed history: {product['asin']}")
        
    except Exception as e:
        log.error(f"Error saving processed product: {e}")

def run_enhanced_pipeline():
    """Run enhanced pipeline with new products and enhanced links"""
    log.info("🚀 ENHANCED PIPELINE STARTED")
    log.info("=" * 60)
    
    try:
        # Import YouTube uploader - we'll create it inline
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        from meta_uploader import MetaUploader
        from tiktok_uploader import TikTokUploader
        from groq_generators import GroqVoiceGenerator
        from video_generator import VideoGenerator
        
        # Initialize uploaders (CI-Safe: Only try YouTube if token or Secret exists)
        yt_up = None
        if Path("token.json").exists() or os.getenv("YT_TOKEN_BASE64"):
            try:
                from youtube_production import ProductionYouTubeUploader
                yt_up = ProductionYouTubeUploader()
            except Exception as e:
                log.warning(f"⚠️ YouTube activation skipped/failed: {e}")
        else:
            log.info("ℹ️ YouTube credentials not found. Skipping YouTube uploader for this run.")

        try:
            from meta_uploader import MetaUploader
            meta_up = MetaUploader()
        except: meta_up = None
        
        try:
            from tiktok_uploader import TikTokUploader
            tt_up = TikTokUploader()
        except: tt_up = None
        
        try:
            from groq_generators import GroqVoiceGenerator
            voice_gen = GroqVoiceGenerator(os.getenv("GROQ_API_KEY"))
        except: voice_gen = None
        
        # Get high-performance products (Discovery 15 -> Score -> Top 3-5)
        log.info("🎯 Step 1: Discovering High-Performance Products...")
        selected_products = get_high_performance_products(count_candidates=15, select_top=5)
        
        if not selected_products:
            log.error("❌ No high-performance products selected")
            return False
        
        log.info(f"✅ Found {len(selected_products)} strategic candidates for production.")
        
        processed_successfully = []

        for product in selected_products:
            log.info("-" * 40)
            log.info(f"📦 Processing: {product['title'][:50]}...")
            log.info(f"💰 Price: {product.get('price', 'N/A')} | Score: {product.get('selection_score', 'N/A')}")
            log.info(f"🔗 Enhanced link: {product['website_link']['link']}")
            
            # Generate script with Diana voice
            try:
                log.info("🎤 Generating script...")
                # We need to use GroqScriptGenerator instead of VoiceGenerator for script
                from groq_generators import GroqScriptGenerator
                gpt_gen = GroqScriptGenerator(os.getenv("GROQ_API_KEY"))
                script = gpt_gen.generate_script(product)
                
                # Generate video with Diana voice
                log.info("🎥 Generating video with Diana voice...")
                video_gen = VideoGenerator()
                voice_path = voice_gen.generate(script['narration'], product['asin'])
                
                if not voice_path:
                    log.error(f"❌ Voice generation failed for {product['asin']}")
                    continue
                    
                video_path = video_gen.generate(product, script, voice_path=voice_path)
                
                if not video_path:
                    log.error(f"❌ Video generation failed for {product['asin']}")
                    continue
                
                log.info(f"✅ Video created: {video_path}")
                
                # Upload to YouTube with enhanced link in description
                if yt_up:
                    log.info("📹 Uploading to YouTube...")
                    desc = f"{script['narration']}\n\n🔥 Check it out: {product['website_link']['link']}\n\n" + " ".join(script.get('hashtags', []))
                    
                    video_id = yt_up.upload_video(
                        video_path, 
                        script['title'], 
                        desc, 
                        script.get('hashtags', []),
                        affiliate_link=product['affiliate_url']
                    )
                    
                    if video_id:
                        log.info(f"✅ YouTube upload successful: {video_id}")
                        product['video_url'] = f"https://youtube.com/shorts/{video_id}"
                        product['video_id'] = video_id
                    else:
                        log.warning("⚠️ YouTube upload failed")
                
                # Upload to social media
                if meta_up:
                    log.info("📸 Uploading to Meta...")
                    meta_up.upload_to_facebook(video_path, f"{script['title']}\n{script['narration']}\n\n{product['website_link']['link']}")
                    meta_up.upload_to_instagram(video_path, f"{script['title']}\n{script['narration']}\n\n{product['website_link']['link']}")
                
                if tt_up:
                    log.info("🎵 Uploading to TikTok...")
                    tt_up.upload_video(video_path, script['title'])
                
                # Mark as successful
                processed_successfully.append(product)
                
                # Send to Make.com webhook
                send_to_make(product)
                
                # Save to processed history
                save_processed_product(product)
                
                # Be respectful between products
                time.sleep(2)

            except Exception as e:
                log.error(f"❌ Error processing {product['asin']}: {e}")
                continue
        
        # Save all successful products to website data at once
        if processed_successfully:
            log.info("🌐 Syncing all successful products to website...")
            update_website_data(processed_successfully)
            
            # Deploy to Cloudflare
            deploy_to_site()
            
            log.info("=" * 60)
            log.info(f"🎉 ENHANCED PIPELINE COMPLETED! ({len(processed_successfully)} products)")
            return True
        else:
            log.error("❌ No products were successfully processed.")
            return False
        
    except Exception as e:
        log.error(f"❌ Enhanced pipeline failed: {e}")
        return False

# Keep existing functions
def get_website_link(product):
    """Legacy function - use enhanced website link instead"""
    enhanced = get_enhanced_website_link(product)
    return enhanced['link']

def send_to_make(product):
    """Sends product data to Make.com"""
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")
    if not webhook_url or "your_webhook" in webhook_url:
        log.warning("⚠️ Make.com Webhook URL not configured. Skipping.")
        return
    
    try:
        log.info(f"⚡ Sending {product['asin']} to Make.com...")
        import requests
        response = requests.post(webhook_url, json=product, timeout=10)
        if response.ok:
            log.info("✓ Webhook sent successfully.")
        else:
            log.error(f"❌ Webhook failed: {response.status_code}")
    except Exception as e:
        log.error(f"❌ Webhook error: {e}")

def update_website_data(new_products):
    """Sync product data to website JSON files with MERGING logic"""
    try:
        site_db = AMAZING_DATA_DIR / "products.json"
        existing_products = []
        
        if site_db.exists():
            try:
                with open(site_db, 'r') as f:
                    existing_products = json.load(f)
                    if not isinstance(existing_products, list):
                        existing_products = []
            except Exception as e:
                log.warning(f"⚠️ Could not load existing products.json: {e}")
        
        # Merge products by ASIN (new ones overwrite old ones if duplicated)
        product_dict = {p['asin']: p for p in existing_products}
        for p in new_products:
            product_dict[p['asin']] = p
            
        merged_list = list(product_dict.values())
        
        # Save to both locations
        with open(DATA_DIR / "products.json", 'w') as f:
            json.dump(merged_list, f, indent=2)
        with open(site_db, 'w') as f:
            json.dump(merged_list, f, indent=2)
        
        log.info(f"✅ Data synchronized to website files ({len(merged_list)} total products)")
        
    except Exception as e:
        log.error(f"❌ Website sync failed: {e}")

def deploy_to_site():
    """Automates Cloudflare Pages deployment"""
    try:
        project_name = os.getenv("CF_PROJECT_NAME", "amazing-cool-finds")
        
        # Use wrangler to deploy
        import subprocess
        result = subprocess.run(
            f"wrangler pages deploy amazing --project-name {project_name}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            log.info("✅ Cloudflare deployment successful")
            return True
        else:
            log.warning(f"⚠️ Cloudflare deployment issue: {result.stderr}")
            return False
            
    except Exception as e:
        log.warning(f"⚠️ Cloudflare deployment failed: {e}")
        return False

def run_pipeline():
    """Run regular pipeline for backward compatibility"""
    return run_enhanced_pipeline()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enhanced Amazing Cool Finds Pipeline")
    parser.add_argument("--run", action="store_true", help="Run enhanced pipeline")
    args = parser.parse_args()
    
    if args.run:
        success = run_enhanced_pipeline()
        sys.exit(0 if success else 1)
    else:
        log.info("Use --run to execute the enhanced pipeline")
        sys.exit(1)