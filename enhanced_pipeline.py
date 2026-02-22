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
import random

# ─── PATHS ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
AMAZING_DATA_DIR = BASE_DIR / "amazing" / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Add core and tools to path for easy imports
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))
sys.path.append(str(BASE_DIR / "tools"))
sys.path.append(str(BASE_DIR / "config"))

# Import custom exceptions
try:
    from groq_generators import GroqQuotaExceeded
except ImportError:
    class GroqQuotaExceeded(Exception): pass

# Import AI Generators
try:
    from groq_generators import GroqProductSelector, GroqScriptGenerator, GroqVoiceGenerator
except ImportError:
    log.warning("⚠️ Could not import Groq generators")

try:
    from gemini_generators import GeminiProductSelector, GeminiScriptGenerator
except ImportError:
    log.warning("⚠️ Could not import Gemini generators")

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

# Global Affiliate Tag
AFFILIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "amazingcool-20")

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
    2. Search candidates (getting basic info like price/rating directly from search).
    3. Score with Groq AI using search info.
    4. Scrape FULL details ONLY for the selected top 3-5 products.
    """
    try:
        from advanced_scraper import AdvancedScraper
        from groq_generators import GroqProductSelector
        from strategy_monitor import StrategyMonitor
        
        scraper = AdvancedScraper(associate_tag=AFFILIATE_TAG)
        
        # Use Gemini if key is available, else fallback to Groq
        gemini_key = os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        if groq_key:
            log.info("🧠 Using Groq for product selection")
            from groq_generators import GroqProductSelector
            selector = GroqProductSelector(groq_key)
        elif gemini_key:
            log.info("💎 Using Gemini for product selection (Groq not available)")
            from gemini_generators import GeminiProductSelector
            selector = GeminiProductSelector(gemini_key)
        else:
            log.error("❌ No AI keys found for selection.")
            return []
            
        monitor = StrategyMonitor(DATA_DIR)
        
        # 0. Get all existing ASINs to prevent duplicates
        existing_asins = get_all_existing_asins()
        log.info(f"🚫 Duplicate Filter: {len(existing_asins)} products already in database.")
        
        # Get strategic target based on priority (Balanced population)
        targets = monitor.get_discovery_priority()
        
        # We'll try to pick candidates from the top 2 priority categories 
        # to ensure the most underserved sections get filled first.
        final_selected = []
        
        # Priority 1: The most empty category
        # Priority 2: The second most empty
        for priority_target in targets[:2]:
            if len(final_selected) >= select_top:
                break
                
            log.info(f"🔍 EQUILIBRIUM MODE: Leveling '{priority_target['category']}' using '{priority_target['keywords']}'")
            
            # 1. Search for candidates with High-Ticket leaning keywords
            search_results = scraper.search(priority_target['keywords'], max_results=10)
            
            if not search_results:
                continue
                
            # 2. Filter out duplicates
            candidates = []
            for item in search_results:
                if item['asin'] in existing_asins:
                    continue
                item['category'] = priority_target['category']
                item['commission'] = monitor.commissions.get(priority_target['category'], '4%')
                candidates.append(item)
            
            if not candidates:
                continue
                
            # 3. AI Selection for this specific category (High Ticket logic)
            log.info(f"🧐 Selecting winner for {priority_target['category']}...")
            selections = []
            
            # Try Groq first (Preferred for viral style)
            if groq_key:
                try:
                    from groq_generators import GroqProductSelector
                    groq_selector = GroqProductSelector(groq_key)
                    selections = groq_selector.analyze_candidates(priority_target['category'], candidates)
                except GroqQuotaExceeded:
                    raise # Re-raise to halt pipeline
                except Exception as e:
                    log.warning(f"🧠 Groq selection failed: {e}. Trying Gemini...")
            
            # Try Gemini if Groq failed or isn't available
            if not selections and gemini_key:
                try:
                    from gemini_generators import GeminiProductSelector
                    gemini_selector = GeminiProductSelector(gemini_key)
                    selections = gemini_selector.analyze_candidates(priority_target['category'], candidates)
                except Exception as e:
                    log.warning(f"💎 Gemini selection failed: {e}. Using heuristic selection.")
            
            # Final fallback: Heuristic (top rated/priced)
            if not selections:
                log.info("⚖️ Using heuristic selection (fallback)")
                candidates.sort(key=lambda x: (float(x.get('rating', 0)), float(x.get('price', '$0').replace('$', '').replace(',', ''))), reverse=True)
                selections = candidates[:3]

            # 4. Enrich selections with FULL details
            for p in selections:
                if len(final_selected) >= select_top:
                    break
                    
                log.info(f"  🕸️  Full extraction for {priority_target['category']} winner: {p['asin']}...")
                details = scraper.get_details(p['asin'])
                
                if not details:
                    continue
                
                # Check image count rule (At least 5 required)
                image_count = len(details.get('images', []))
                if image_count < 5:
                    log.warning(f"⚠️ Skipping {p['asin']} due to image count: {image_count} (Rule: At least 5 images required)")
                    continue
                
                # Merge details back, preserving selection metadata
                p.update(details)
                p['website_link'] = get_enhanced_website_link(p)
                p['affiliate_url'] = f"https://www.amazon.com/dp/{p['asin']}?tag={AFFILIATE_TAG}"
                p['processed_at'] = datetime.now().isoformat()
                final_selected.append(p)
                existing_asins.add(p['asin']) # Prevent duplicates in same run
                
                # Polite delay between full scrapes
                time.sleep(random.uniform(3, 7))
            
        return final_selected

    except Exception as e:
        import traceback
        log.error(f"Error in high-performance selection: {e}")
        log.error(traceback.format_exc())
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
    """Run enhanced pipeline with robust error handling and reporting"""
    log.info("🚀 STARTING ENHANCED AUTOMATED PIPELINE...")
    log.info("=" * 60)
    
    success_count = 0
    failure_count = 0
    processed_successfully = []
    
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
        
        # Step 1: Discover products
        log.info("🎯 Step 1: Discovering Strategic Candidates...")
        try:
            selected_products = get_high_performance_products(count_candidates=15, select_top=5)
        except GroqQuotaExceeded as e:
            log.error(f"🛑 ABORTING: {e}")
            return False
            
        if not selected_products:
            log.error("❌ No strategic products found today.")
            return False
            
        log.info(f"✨ Found {len(selected_products)} strategic candidates. Starting production...")
        
        processed_successfully = []

        for product in selected_products:
            try:
                # 2. Scripting
                log.info("🎤 Generating script...")
                gemini_key = os.getenv("GEMINI_API_KEY")
                groq_key = os.getenv("GROQ_API_KEY")
                script = None
                
                # Try Groq first (Mandatory per configuration)
                if groq_key:
                    try:
                        from groq_generators import GroqScriptGenerator
                        gpt_gen = GroqScriptGenerator(groq_key)
                        script = gpt_gen.generate_script(product)
                    except GroqQuotaExceeded:
                        raise # Halt if quota empty
                    except Exception as e:
                        log.warning(f"🧠 Groq Scripting failed: {e}. Trying Gemini...")
                
                # Fallback to Gemini only if Groq is literally broken/timeout
                if not script and gemini_key:
                    try:
                        from gemini_generators import GeminiScriptGenerator
                        gpt_gen = GeminiScriptGenerator(gemini_key)
                        script = gpt_gen.generate_script(product)
                    except Exception as e:
                        log.error(f"💎 Gemini Scripting also failed: {e}")
                
                if not script:
                    log.error(f"❌ All script generation attempts failed for {product['asin']}")
                    failure_count += 1
                    continue
                product['script'] = script
                
                # 3. Voiceover (Neural Groq Diana)
                log.info("🗣️  Generating voiceover...")
                if not voice_gen:
                    log.error(f"⚠️ Voice generator not initialized. Skipping {product['asin']}.")
                    failure_count += 1
                    continue

                voice_path = voice_gen.generate(script['narration'], product['asin'])
                
                if not voice_path:
                    log.error(f"⚠️ Voiceover failed for {product['asin']}. Skipping.")
                    failure_count += 1
                    continue
                product['voice_path'] = voice_path
                
                # 4. Video production
                log.info("🎥 Generating video...")
                from video_generator import VideoGenerator
                video_gen_instance = VideoGenerator()
                video_path = video_gen_instance.generate(product, script, voice_path=voice_path)
                
                if not video_path:
                    log.error(f"❌ Video production failed for {product['asin']}")
                    failure_count += 1
                    continue
                
                # 5. Distribution
                # 5.1 YouTube
                if yt_up:
                    log.info("📹 Uploading to YouTube...")
                    try:
                        desc = f"{script['narration']}\n\n🔥 Check it out: {product['website_link']['link']}\n\n" + " ".join(script.get('hashtags', []))
                        yt_up.upload_video(video_path, script['title'], desc, script.get('hashtags', []), affiliate_link=product['affiliate_url'])
                    except Exception as e:
                        log.warning(f"⚠️ YouTube upload failed: {e}")

                # 5.2 Meta (Facebook & Instagram)
                if meta_up:
                    log.info("📸 Uploading to Meta (FB/IG)...")
                    caption = f"{script['narration']}\n\nProduct: {product['website_link']['link']}\n\n" + " ".join(script.get('hashtags', []))
                    try:
                        meta_up.upload_to_facebook(video_path, caption)
                        meta_up.upload_to_instagram(video_path, caption)
                    except Exception as e:
                        log.warning(f"⚠️ Meta upload failed: {e}")

                # 5.3 TikTok
                if tt_up:
                    log.info("🎵 Uploading to TikTok...")
                    try:
                        tt_up.upload_video(video_path, script['title'])
                    except Exception as e:
                        log.warning(f"⚠️ TikTok upload failed: {e}")

                # Tracking & Success logic
                processed_successfully.append(product)
                send_to_make(product)
                save_processed_product(product)
                success_count += 1
                log.info(f"✅ Finished production & distribution for {product['asin']}!")
                time.sleep(5) # Give APIs a breather

            except GroqQuotaExceeded as e:
                log.error(f"🛑 STOPPING PIPELINE: Groq Quota hit. Will retry in next scheduled run. Error: {e}")
                # We stop processing more products to save quota and wait for refresh
                break 
            except Exception as e:
                log.error(f"❌ Error processing {product['asin']}: {e}")
                failure_count += 1
                continue
        
        # Save all successful products to website data at once
        if processed_successfully:
            log.info(f"🌐 Syncing {len(processed_successfully)} products to website...")
            update_website_data(processed_successfully)
            deploy_to_site()
            
            log.info("=" * 60)
            log.info("📊 PIPELINE EXECUTION SUMMARY")
            log.info(f"🟢 Successes: {success_count}")
            log.info(f"🔴 Failures:  {failure_count}")
            log.info(f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}")
            log.info("=" * 60)
            return True
        else:
            log.error("❌ Pipeline finished with 0 successes.")
            return False
        
    except Exception as e:
        log.error(f"❌ Enhanced pipeline failed: {e}")
        return False

# Keep existing functions
def get_website_link(product):
    """Legacy function - use enhanced website link instead"""
    enhanced = get_enhanced_website_link(product)
    return enhanced['link']

def serialize_for_json(obj):
    """Convert non-serializable objects to JSON-compatible format"""
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

def send_to_make(product):
    """Sends product data to Make.com"""
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")
    if not webhook_url or "your_webhook" in webhook_url:
        log.warning("⚠️ Make.com Webhook URL not configured. Skipping.")
        return
    
    try:
        log.info(f"⚡ Sending {product['asin']} to Make.com...")
        import requests
        # Serialize product data to ensure JSON compatibility
        clean_product = serialize_for_json(product)
        response = requests.post(webhook_url, json=clean_product, timeout=10)
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
        
        # Serialize new products to ensure JSON compatibility
        clean_new_products = [serialize_for_json(p) for p in new_products]
        
        # Merge products by ASIN (new ones overwrite old ones if duplicated)
        product_dict = {p['asin']: p for p in existing_products}
        for p in clean_new_products:
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
    """Automates Cloudflare Pages deployment using the shared deploy script"""
    try:
        deploy_script = Path(__file__).parent / "tools" / "deploy.sh"
        if not deploy_script.exists():
            log.warning("⚠️ Deploy script not found, falling back to direct wrangler command.")
            project_name = os.getenv("CF_PROJECT_NAME", "amazing-cool-finds")
            cmd = f"npx wrangler pages deploy amazing --project-name {project_name}"
        else:
            cmd = f"bash {deploy_script}"
        
        # Try up to 3 times
        import subprocess
        for attempt in range(3):
            log.info(f"☁️  Deploying to Cloudflare Pages (Attempt {attempt+1}/3)...")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                log.info("✅ Cloudflare deployment successful!")
                return True
            else:
                log.warning(f"⚠️ Deployment attempt {attempt+1} failed: {result.stderr}")
                if attempt < 2:
                    time.sleep(10) # Wait 10s before retry
        
        log.error("❌ Cloudflare deployment failed after 3 attempts.")
        return False
            
    except Exception as e:
        log.error(f"❌ Cloudflare deployment error: {e}")
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