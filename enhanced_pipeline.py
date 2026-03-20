#!/usr/bin/env python3
"""
UPDATED PIPELINE - Enhanced website links with unique IDs and new products
"""
import os
import sys
import json
import time
import logging
import threading
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
class CriticalPipelineError(Exception):
    """Exception raised when a critical pipeline step fails."""
    pass

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

try:
    from openrouter_generators import OpenRouterProductSelector, OpenRouterScriptGenerator
except ImportError:
    log.warning("⚠️ Could not import OpenRouter generators")

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

# ─── SUPABASE CLIENT ─────────────────────────────────────────────
def get_supabase_client():
    """Initialize Supabase client if credentials available"""
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if supabase_url and supabase_key:
            return create_client(supabase_url, supabase_key)
    except Exception as e:
        log.warning(f"⚠️ Supabase client init failed: {e}")
    return None

# Initialize Supabase client
supabase_client = get_supabase_client()
if supabase_client:
    log.info("✅ Supabase client initialized")
else:
    log.info("ℹ️ Supabase not available - skipping database logging")

def log_to_supabase(table_name, data):
    """Log data to Supabase table"""
    if not supabase_client:
        return False
    try:
        supabase_client.table(table_name).insert(data).execute()
        return True
    except Exception as e:
        log.warning(f"⚠️ Failed to log to {table_name}: {e}")
        return False

# Global Affiliate Tag
AFFILIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "amazingcool-20")

# ─── CONFIGURATION ───────────────────────────────────────────────
PRODUCT_TARGETS = [
    {"category": "Tech", "keywords": "premium tech gadgets 2026", "commission": "4%"},
    {"category": "Life & Style", "keywords": "luxury skincare beauty essentials", "commission": "10%"},
    {"category": "Home & Auto", "keywords": "modern home decor luxury office equipment", "commission": "4%"},
]

# ─── ENHANCED FUNCTIONS ─────────────────────────────────────
def get_enhanced_website_link(product):
    """Generate enhanced website link with scroll to product card"""
    base_url = os.getenv("WEBSITE_URL", "https://amazing-cool-finds.com")
    
    # Direct link with hash scroll to product card
    enhanced_link = f"{base_url}/#product-{product['asin']}"
    
    return {
        'link': enhanced_link,
        'scroll_target': f"product-{product['asin']}",
        'full_url': enhanced_link
    }

def get_high_performance_products(count_candidates=15, select_top=3, min_price=60):
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
        
        # Use OpenRouter if key is available, else fallback to Groq
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        if openrouter_key:
            openrouter_key = openrouter_key.strip()
            log.info("🤖 Using OpenRouter (Claude) for product selection")
            from openrouter_generators import OpenRouterProductSelector
            selector = OpenRouterProductSelector(openrouter_key)
        elif groq_key:
            groq_key = groq_key.strip()
            log.info("🧠 Using Groq for product selection (OpenRouter not available)")
            from groq_generators import GroqProductSelector
            selector = GroqProductSelector(groq_key)
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
                log.warning(f"⚠️ No search results for '{priority_target['keywords']}'")
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
                log.info(f"ℹ️ All found products for {priority_target['category']} are already in database.")
                continue
                
            # 3. AI Selection for this specific category (High Ticket logic)
            log.info(f"🧐 Selecting winner for {priority_target['category']}...")
            selections = []
            
            # Try OpenRouter first (Better reasoning for selection)
            openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
            if openrouter_key:
                try:
                    from openrouter_generators import OpenRouterProductSelector
                    openrouter_selector = OpenRouterProductSelector(openrouter_key)
                    selections = openrouter_selector.analyze_candidates(priority_target['category'], candidates)
                except Exception as e:
                    error_msg = str(e).lower()
                    if "429" in error_msg or "quota" in error_msg:
                        log.warning(f"🤖 OpenRouter Quota Exceeded during selection. Falling back to Groq...")
                    else:
                        log.warning(f"🤖 OpenRouter selection failed: {e}. Trying Groq...")
            
            # Try Groq if OpenRouter failed or isn't available
            if not selections and groq_key:
                try:
                    from groq_generators import GroqProductSelector
                    groq_selector = GroqProductSelector(groq_key)
                    selections = groq_selector.analyze_candidates(priority_target['category'], candidates)
                except GroqQuotaExceeded:
                    log.error("🛑 Groq Quota Exceeded during selection.")
                except Exception as e:
                    log.warning(f"🧠 Groq selection failed: {e}. Using heuristic selection.")
            
            # Final fallback: Heuristic (top rated/priced)
            if not selections:
                log.info("⚖️ Using heuristic selection (fallback)")
                # Sort by price then rating
                def sort_val(x):
                    try: return float(x.get('price', '$0').replace('$', '').replace(',', ''))
                    except: return 0.0
                candidates.sort(key=lambda x: (sort_val(x), float(x.get('rating', 0))), reverse=True)
                selections = candidates[:3]

            # 4. Enrich selections with FULL details
            for p in selections:
                if len(final_selected) >= select_top:
                    break
                    
                log.info(f"  🕸️  Full extraction for {priority_target['category']} winner: {p['asin']}...")
                details = scraper.get_details(p['asin'])
                
                if not details:
                    log.warning(f"⚠️ Could not extract details for {p['asin']}")
                    continue
                
                # Check image count rule (At least 5 required)
                image_count = len(details.get('images', []))
                if image_count < 5:
                    log.warning(f"⚠️ Skipping {p['asin']} due to image count: {image_count} (Rule: At least 5 images required)")
                    continue

                # Rigorous Price Rule: Min price (Dynamic)
                price_str = details.get('price', '$0').replace('$', '').replace(',', '')
                try:
                    price_val = float(price_str)
                    if price_val < min_price:
                        log.warning(f"⚠️ Skipping {p['asin']} due to price: ${price_val} (Required: ${min_price})")
                        continue
                except:
                    log.warning(f"⚠️ Could not verify price for {p['asin']}: {details.get('price')}. Skipping product.")
                    continue
                
                # Merge details back, preserving selection metadata
                p.update(details)
                
                # AI Re-categorization (Robust alignment)
                try:
                    log.info(f"🧠 AI Re-categorizing {p['asin']}...")
                    p['category'] = selector.classify_product(p)
                    log.info(f"📌 Final Category: {p['category']}")
                except Exception as e:
                    log.warning(f"⚠️ AI re-categorization failed: {e}. Keeping original: {p['category']}")

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
    
    # Check main products file
    for db_path in [AMAZING_DATA_DIR / "products.json", DATA_DIR / "products.json", DATA_DIR / "processed_products.json"]:
        if db_path.exists():
            try:
                with open(db_path, 'r') as f:
                    data = json.load(f)
                    for item in data: 
                        if isinstance(item, dict) and 'asin' in item:
                            existing.add(item['asin'])
            except: pass
        
    return existing

def get_recent_asins():
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
    """Save COMPLETE product data to processed history (not just minimal data)"""
    try:
        history_file = DATA_DIR / "processed_products.json"
        processed = []
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    processed = json.load(f)
                if not isinstance(processed, list):
                    processed = []
            except:
                processed = []
        
        # Clean and serialize product for JSON (handles Path objects, etc.)
        clean_product = serialize_for_json(product)
        
        # ALWAYS save COMPLETE product data including images, price, script, category, etc.
        # If category is missing, try to derive from title or use 'Life & Style' as default
        product_category = clean_product.get('category')
        if not product_category or product_category == 'unknown':
            title = clean_product.get('title', '').lower()
            if any(w in title for w in ['laptop', 'phone', 'tablet', 'headphone', 'camera', 'gaming', 'monitor', 'keyboard', 'mouse', 'smart', 'tech', 'electronic']):
                product_category = 'Tech'
            elif any(w in title for w in ['dash', 'car', 'auto', 'vehicle']):
                product_category = 'Home & Auto'
            else:
                product_category = 'Life & Style'
            log.info(f"🔄 Derived category for {clean_product.get('asin')}: {product_category}")
        
        asin = clean_product.get('asin', '')
        images = clean_product.get('images', [])
        image_url = clean_product.get('image_url', '')
        
        if not images and asin:
            image_url = f"https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&Format=_SL600_&ASIN={asin}&MarketPlace=US&ID=AsinImage&WS=1"
            images = [image_url]
        
        full_product_data = {
            'asin': asin,
            'title': clean_product.get('title'),
            'price': clean_product.get('price'),
            'rating': clean_product.get('rating'),
            'reviews_count': clean_product.get('reviews_count'),
            'category': product_category,
            'images': images,
            'image_url': image_url,
            'bullets': clean_product.get('bullets', []),
            'affiliate_url': clean_product.get('affiliate_url'),
            'processed_at': clean_product.get('processed_at'),
            'website_link': clean_product.get('website_link'),
            'script': clean_product.get('script'),
            'youtube_video_id': clean_product.get('youtube_video_id'),
            'youtube_url': clean_product.get('youtube_url'),
        }
        
        # Check if product already exists (update) or is new (append)
        asins = [p.get('asin') for p in processed]
        existing_idx = asins.index(full_product_data['asin']) if full_product_data['asin'] in asins else -1
        
        if existing_idx >= 0:
            processed[existing_idx] = full_product_data
        else:
            processed.append(full_product_data)
        
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
        
        # Initialize uploaders
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
        
        # Upload-Post (multi-platform uploader)
        uploadpost_up = None
        uploadpost_key = os.getenv("UPLOADPOST_API_KEY")
        if uploadpost_key:
            try:
                from uploadpost_uploader import UploadPostUploader
                uploadpost_up = UploadPostUploader(uploadpost_key)
                log.info("🚀 Upload-Post multi-platform uploader activated!")
            except Exception as e:
                log.warning(f"⚠️ Upload-Post activation failed: {e}")
        
        try:
            from groq_generators import GroqVoiceGenerator
            voice_gen = GroqVoiceGenerator(os.getenv("GROQ_API_KEY"))
        except: voice_gen = None
        
        # Step 1: Discover products with dynamic fallback
        log.info("🎯 Step 1: Discovering Strategic Candidates...")
        selected_products = []
        price_thresholds = [50, 35, 20] # Try high-ticket first, then mid, then low-mid
        
        for threshold in price_thresholds:
            try:
                log.info(f"🔍 Attempting production run with ${threshold} minimum price...")
                selected_products = get_high_performance_products(count_candidates=15, select_top=5, min_price=threshold)
                if selected_products:
                    log.info(f"✅ Found {len(selected_products)} products with ${threshold} threshold.")
                    break
                else:
                    log.warning(f"⚠️ No products found at ${threshold}. Retrying with lower threshold...")
            except GroqQuotaExceeded as e:
                log.error(f"🛑 Groq Quota hit during discovery: {e}")
                # We can't do much if both AIs (Gemini/Groq) are failing quota, 
                # but let's see if we can continue with what we have (nothing yet)
                break
            except Exception as e:
                log.error(f"❌ Error during discovery at ${threshold}: {e}")
                continue
            
        if not selected_products:
            log.error("❌ No strategic products found today after all attempts.")
            return False
            
        log.info(f"✨ Found {len(selected_products)} strategic candidates. Starting production...")
        
        processed_successfully = []

        for product in selected_products:
            try:
                # 2. Scripting (OpenRouter)
                log.info("🎤 Generating script (OpenRouter)...")
                openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
                script = None
                
                if not openrouter_key:
                    raise CriticalPipelineError("❌ OPENROUTER_API_KEY is missing. Cannot generate script.")
                
                try:
                    from openrouter_generators import OpenRouterScriptGenerator
                    gpt_gen = OpenRouterScriptGenerator(openrouter_key)
                    script = gpt_gen.generate_script(product)
                except Exception as e:
                    log.error(f"🤖 OpenRouter Scripting failed: {e}")
                    raise CriticalPipelineError(f"Script generation failed for {product['asin']} using OpenRouter.")
                
                if not script:
                    log.error(f"❌ OpenRouter returned empty script for {product['asin']}")
                    raise CriticalPipelineError(f"Empty script from OpenRouter for {product['asin']}.")
                
                product['script'] = script
                
                # 3. Voiceover (Groq Diana)
                log.info("🗣️  Generating voiceover (Groq)...")
                if not voice_gen:
                    raise CriticalPipelineError("❌ Voice generator (Groq) not initialized.")

                try:
                    voice_path = voice_gen.generate(script['narration'], product['asin'])
                except GroqQuotaExceeded:
                    raise
                except Exception as e:
                    log.error(f"🧠 Groq Voiceover failed: {e}")
                    raise CriticalPipelineError(f"Voiceover generation failed for {product['asin']} using Groq.")
                
                if not voice_path:
                    log.error(f"⚠️ Voiceover returned None for {product['asin']}")
                    raise CriticalPipelineError(f"Empty voiceover from Groq for {product['asin']}.")
                
                product['voice_path'] = voice_path
                
                # VALIDATION: Check all prerequisites before creating video
                image_count = len(product.get('images', []))
                if image_count < 4:
                    log.error(f"⛔ SKIPPED: {product['asin']} has only {image_count} images (minimum 4 required)")
                    failure_count += 1
                    processed_successfully.append({
                        'asin': product['asin'],
                        'status': 'skipped',
                        'reason': f'Insufficient images: {image_count}/4'
                    })
                    continue
                
                log.info(f"✅ Validation passed: script ✓, voice ✓, images ({image_count}) ✓")
                
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
                        video_id = yt_up.upload_video(video_path, script['title'], desc, script.get('hashtags', []), affiliate_link=product['affiliate_url'])
                        if video_id:
                            product['youtube_uploaded'] = True
                            product['youtube_video_id'] = video_id
                            product['youtube_url'] = f"https://youtube.com/watch?v={video_id}"
                            log.info(f"✅ YouTube metadata saved for {product['asin']}")
                            
                            # Parallel website update
                            threading.Thread(target=update_website_parallel, args=(product,), daemon=True).start()
                    except Exception as e:
                        log.warning(f"⚠️ YouTube upload failed: {e}")

                # 5.1b Upload-Post (Multi-platform)
                if uploadpost_up:
                    log.info("🚀 Uploading to multiple platforms via Upload-Post...")
                    try:
                        desc = f"{script['narration']}\n\n🔥 Check it out: {product['website_link']['link']}\n\n" + " ".join(script.get('hashtags', []))
                        platforms = ["instagram", "facebook", "pinterest"]
                        result = uploadpost_up.upload_from_url(
                            video_url=video_path,
                            title=script['title'],
                            description=desc,
                            platforms=platforms,
                            affiliate_link=product['affiliate_url']
                        )
                        if result and result.get('success'):
                            results = result.get('results', {})
                            for platform, data in results.items():
                                if data.get('success'):
                                    log.info(f"✅ Upload-Post: {platform} - {data.get('url', 'OK')}")
                                    if platform == 'youtube':
                                        product['youtube_uploaded'] = True
                                        product['youtube_url'] = data.get('url')
                            log.info(f"🚀 Upload-Post completed: {len([r for r in results.values() if r.get('success')])}/{len(platforms)} platforms")
                        else:
                            log.warning(f"⚠️ Upload-Post failed: {result}")
                    except Exception as e:
                        log.warning(f"⚠️ Upload-Post error: {e}")

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

                # Log to Supabase
                log_to_supabase("products", {
                    "asin": product.get("asin"),
                    "title": product.get("title"),
                    "price": product.get("price"),
                    "rating": product.get("rating"),
                    "reviews_count": product.get("reviews_count"),
                    "category": product.get("category"),
                    "affiliate_url": product.get("affiliate_url"),
                    "website_link": product.get("website_link", {}).get("link") if isinstance(product.get("website_link"), dict) else None,
                    "script_title": product.get("script", {}).get("title") if isinstance(product.get("script"), dict) else None,
                    "video_path": str(product.get("video_path")) if product.get("video_path") else None,
                    "youtube_uploaded": product.get("youtube_uploaded", False),
                    "youtube_video_id": product.get("youtube_video_id"),
                    "youtube_url": product.get("youtube_url"),
                    "processed_at": product.get("processed_at")
                })

                success_count += 1
                log.info(f"✅ Finished production & distribution for {product['asin']}!")
                time.sleep(5) # Give APIs a breather

            except CriticalPipelineError as e:
                log.error(f"🛑 CRITICAL FAILURE: {e}. Stopping pipeline to retry later.")
                # We stop the entire pipeline as per user requirement
                raise e 
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

            # Log cycle metrics to Supabase
            log_to_supabase("cycle_metrics", {
                "run_date": datetime.now().isoformat(),
                "success_count": success_count,
                "failure_count": failure_count,
                "products_processed": len(processed_successfully),
                "youtube_uploaded": sum(1 for p in processed_successfully if p.get("youtube_uploaded")),
                "meta_uploaded": sum(1 for p in processed_successfully if p.get("meta_uploaded")),
                "tiktok_uploaded": sum(1 for p in processed_successfully if p.get("tiktok_uploaded"))
            })

            return True
        else:
            log.error("❌ Pipeline finished with 0 successes.")
            return False
        
    except CriticalPipelineError as e:
        log.error(f"❌ Pipeline halted due to critical AI failure: {e}")
        # CRITICAL: Save any successful products even if pipeline fails
        if processed_successfully:
            log.warning(f"💾 Saving {len(processed_successfully)} successful products before exit...")
            update_website_data(processed_successfully)
        return False
    except Exception as e:
        log.error(f"❌ Enhanced pipeline failed: {e}")
        # CRITICAL: Save any successful products even if pipeline fails
        if processed_successfully:
            log.warning(f"💾 Saving {len(processed_successfully)} successful products before exit...")
            update_website_data(processed_successfully)
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
        
        # Ensure images is a proper array
        images = product.get('images', [])
        if isinstance(images, list):
            clean_product['product_images'] = images
            clean_product['image_count'] = len(images)
        
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
        
        # If website has very few products, try to restore from processed_products.json as base
        if len(existing_products) < 5:
            processed_file = DATA_DIR / "processed_products.json"
            if processed_file.exists():
                try:
                    with open(processed_file, 'r') as f:
                        backup_products = json.load(f)
                    if len(backup_products) > len(existing_products):
                        log.info(f"🔄 Restoring {len(backup_products)} products from processed history as base")
                        existing_products = backup_products
                except: pass
        
        # Protect existing products - never lose them if we have enough
        if len(existing_products) >= 50 and new_products and len(new_products) < 3:
            log.warning(f"⚠️ Refusing to overwrite {len(existing_products)} products with only {len(new_products)} new. Keeping existing.")
            return  # Don't save if we might lose data
        
        # Serialize new products to ensure JSON compatibility
        clean_new_products = [serialize_for_json(p) for p in new_products] if new_products else []
        
        # Filter NEW products without images (can't create video without images)
        valid_new_products = [p for p in clean_new_products if p.get('images') and len(p.get('images', [])) > 0]
        invalid_new_count = len(clean_new_products) - len(valid_new_products)
        if invalid_new_count > 0:
            log.warning(f"⚠️ {invalid_new_count} new products skipped - no images (can't create video)")
        
        # Merge ALL products for website (existing + new, with or without images)
        product_dict = {p['asin']: p for p in existing_products}
        for p in valid_new_products:
            product_dict[p['asin']] = p
        
        merged_list = list(product_dict.values())
        
        # ALWAYS ensure all products have images and links
        for p in merged_list:
            asin = p.get('asin', '')
            if asin:
                # Add fallback image if missing
                if not p.get('image_url'):
                    p['image_url'] = f"https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&Format=_SL600_&ASIN={asin}&MarketPlace=US&ID=AsinImage&WS=1"
                if not p.get('images'):
                    p['images'] = [p['image_url']]
                # Add affiliate link if missing
                if not p.get('affiliate_url'):
                    p['affiliate_url'] = f"https://www.amazon.com/dp/{asin}?tag={AFFILIATE_TAG}"
        
        # Fix missing categories for all products
        no_cat_count = 0
        for p in merged_list:
            if not p.get('category') or p.get('category') == 'unknown':
                title = p.get('title', '').lower()
                if any(w in title for w in ['laptop', 'phone', 'tablet', 'headphone', 'camera', 'gaming', 'monitor', 'keyboard', 'mouse', 'smart', 'tech', 'electronic']):
                    p['category'] = 'Tech'
                elif any(w in title for w in ['dash', 'car', 'auto', 'vehicle']):
                    p['category'] = 'Home & Auto'
                else:
                    p['category'] = 'Life & Style'
                no_cat_count += 1
        
        if no_cat_count > 0:
            log.warning(f"🔄 Fixed {no_cat_count} products with missing category")
        
        log.info(f"🔄 Website: {len(existing_products)} existing + {len(valid_new_products)} new valid = {len(merged_list)} total")
        
        # If existing products are very few and we have new valid products, use only new
        if len(existing_products) < 10 and len(valid_new_products) > 0:
            log.info(f"🔄 Replacing {len(existing_products)} old products with {len(valid_new_products)} new valid products")
            merged_list = valid_new_products
            
        # Save to both locations
        with open(DATA_DIR / "products.json", 'w') as f:
            json.dump(merged_list, f, indent=2)
        with open(site_db, 'w') as f:
            json.dump(merged_list, f, indent=2)
        
        log.info(f"✅ Data synchronized to website files ({len(merged_list)} total products)")
        
        # Trigger parallel deployment
        threading.Thread(target=deploy_to_site, daemon=True).start()
        
    except Exception as e:
        log.error(f"❌ Website sync failed: {e}")

def update_website_parallel(product):
    """Update single product to website immediately in background"""
    try:
        import fcntl
        site_db = AMAZING_DATA_DIR / "products.json"
        lock_file = AMAZING_DATA_DIR / "products.json.lock"
        
        # Create lock file
        lock_file.touch(exist_ok=True)
        
        with open(lock_file, 'r+') as lock_f:
            try:
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
                
                if site_db.exists():
                    try:
                        with open(site_db, 'r') as f:
                            products = json.load(f)
                    except json.JSONDecodeError:
                        log.warning(f"⚠️ Corrupted JSON in website DB, creating new file")
                        products = []
                else:
                    products = []
                
                asins = [p.get('asin') for p in products]
                if product.get('asin') not in asins:
                    # Serialize product to ensure JSON compatibility (convert Path objects, etc.)
                    clean_product = serialize_for_json(product)
                    products.append(clean_product)
                    with open(site_db, 'w') as f:
                        json.dump(products, f, indent=2)
                    log.info(f"🌐 [Parallel] Product {product.get('asin')} added to website")
                
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
            except Exception as e:
                log.warning(f"⚠️ Lock error in parallel update: {e}")
                
    except Exception as e:
        log.warning(f"⚠️ Parallel website update failed: {e}")

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
