#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          LIVEITUPDEALS — AUTOMATED AFFILIATE PIPELINE           ║
║     Amazon Products → AI Script → Video → YouTube Shorts        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── PATHS ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
VIDEOS_DIR = BASE_DIR / "output_videos"
IMAGES_DIR = BASE_DIR / "output_images"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

for d in [VIDEOS_DIR, IMAGES_DIR, LOGS_DIR, DATA_DIR]:
    d.mkdir(exist_ok=True)

# ─── ENV & LOGGING ───────────────────────────────────────────────
load_dotenv(BASE_DIR / ".env")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log"),
        logging.StreamHandler()
    ])
log = logging.getLogger("LivItUp")

# ─── CONFIGURATION ───────────────────────────────────────────────
PRODUCT_TARGETS = [
    {"category": "Beauty", "keywords": "luxury beauty skincare premium", "commission": "10%"},
    {"category": "Beauty", "keywords": "luxury perfume fragrance high end", "commission": "10%"},
    {"category": "Electronics", "keywords": "premium tech gadgets 2025", "commission": "4%"},
    {"category": "Clothing", "keywords": "luxury fashion men premium jacket", "commission": "4%"},
    {"category": "Clothing", "keywords": "luxury fashion women premium dress", "commission": "4%"},
    {"category": "Home", "keywords": "premium home decor luxury modern", "commission": "3%"},
    {"category": "Electronics", "keywords": "premium laptop high end 2025", "commission": "3%"},
    {"category": "Electronics", "keywords": "luxury smartwatch premium 2025", "commission": "4%"},
]

ITEMS_PER_SEARCH = 3
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_DURATION_SECS = 15

# ─── AMAZON FETCHER ───────────────────────────────────────────────
class AmazonFetcher:
    def __init__(self):
        self.access_key = os.getenv("AMAZON_ACCESS_KEY")
        self.secret_key = os.getenv("AMAZON_SECRET_KEY")
        self.associate_tag = os.getenv("AMAZON_ASSOCIATE_TAG")
        if not all([self.access_key, self.secret_key, self.associate_tag]):
            raise EnvironmentError("Missing Amazon credentials in .env")

    def search(self, keywords: str, search_index: str = "All", count: int = 3) -> list[dict]:
        try:
            from amazon_paapi import AmazonApi
            
            api = AmazonApi(
                key=self.access_key,
                secret=self.secret_key,
                tag=self.associate_tag,
                country="US"
            )
            
            results = api.search_items(
                keywords=keywords,
                search_index=search_index,
                item_count=count,
                resources=[
                    "images.primary.large",
                    "images.variants.large",
                    "itemInfo.title",
                    "itemInfo.features",
                    "offersV2.listings.price",
                    "customerReviews.starRating",
                ]
            )
            
            products = []
            if results and results.items:
                for item in results.items:
                    try:
                        title = item.item_info.title.display_value if item.item_info and item.item_info.title else "Product"
                        
                        # Get price
                        price = "Check Price"
                        if item.offers and item.offers.listings:
                            try:
                                price = item.offers.listings[0].price.display_amount
                            except:
                                pass
                        
                        # Get rating
                        rating = "4.5"
                        if item.customer_reviews and item.customer_reviews.star_rating:
                            try:
                                rating = str(item.customer_reviews.star_rating.value)
                            except:
                                pass
                        
                        # Get image
                        image = None
                        if item.images and item.images.primary:
                            try:
                                image = item.images.primary.large.url
                            except:
                                pass
                        
                        # Get affiliate URL
                        url = item.detail_page_url if hasattr(item, 'detail_page_url') else f"https://www.amazon.com/dp/{item.asin}?tag={self.associate_tag}"
                        
                        if image:
                            products.append({
                                "asin": item.asin,
                                "title": title,
                                "price": price,
                                "rating": str(rating),
                                "image_url": image,
                                "affiliate_url": url
                            })
                    except Exception as e:
                        log.warning(f"Skipping malformed product: {e}")
                        continue
            
            log.info(f"✓ Amazon returned {len(products)} products for '{keywords}'")
            return products
        except ImportError:
            log.error("amazon_paapi not installed. Run: pip install python-amazon-paapi")
            return []
        except Exception as e:
            log.error(f"Amazon API error: {e}")
            return []

# ─── GEMINI SCRIPT GENERATOR ─────────────────────────────────────
class ScriptGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("Missing GEMINI_API_KEY in .env")
        import google.generativeai as gemini
        gemini.configure(api_key=self.api_key)
    
    def generate(self, product: dict) -> dict:
        try:
            prompt = f"""
You are a viral short-form video script writer for a luxury product showcase channel.
Write a script for a 15-second faceless product video. Be direct, create urgency, and be aspirational.

IMPORTANT: Write ALL content in ENGLISH only.

Product: {product['title']}
Price: {product['price']}
Rating: {product['rating']} stars

Return ONLY valid JSON with these exact keys (no extra text):
{{
  "title": "Video title in ENGLISH (max 60 chars, include emoji)",
  "hook": "First 2 seconds text overlay in ENGLISH — attention grabber (max 8 words)",
  "body": "Main text shown 3-12 seconds in ENGLISH (max 25 words, punchy)",
  "cta": "Call to action text overlay in ENGLISH (max 6 words)",
  "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}
"""
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            raw = response.text.strip()
            # Remove markdown code blocks if present
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1].rsplit('\n```', 1)[0]
            script = json.loads(raw)
            log.info(f"✓ Script generated: {script['title']}")
            return script
        except Exception as e:
            log.error(f"Script generation failed: {e}")
            return {
                "title": f"🔥 {product['title'][:50]}",
                "hook": "Wait for it...",
                "body": f"Only {product['price']} — {product['rating']}★ rated. Link in bio.",
                "cta": "Don't sleep on this",
                "hashtags": ["luxury", "deals", "amazon", "liveitupdeals", "fyp"]
            }

# ─── MAIN PIPELINE ORCHESTRATOR ───────────────────────────────────
def run_pipeline(update_website_only=False):
    log.info("=" * 60)
    log.info("🚀 LIVEITUPDEALS PIPELINE STARTED")
    log.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"   Mode: {'Website Update Only' if update_website_only else 'Full Pipeline'}")
    log.info("=" * 60)
    
    try:
        amazon = AmazonFetcher()
        scripts = ScriptGenerator()
        
        all_products = []
        
        for target in PRODUCT_TARGETS:
            log.info(f"\n🔍 Searching {target['category']}: {target['keywords']}")
            products = amazon.search(
                keywords=target['keywords'],
                search_index=target['category'],
                count=ITEMS_PER_SEARCH
            )
            
            for product in products:
                product['category'] = target['category']
                product['commission'] = target['commission']
                all_products.append(product)
                
                if not update_website_only:
                    # Generate script for video
                    script = scripts.generate(product)
                    log.info(f"  Script: {script['title']}")
                    # TODO: Generate video, upload to YouTube
            
            time.sleep(1)  # Respect API rate limits
        
        # Save products to JSON for website
        products_file = DATA_DIR / "products.json"
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        log.info(f"\n✅ Saved {len(all_products)} products to {products_file}")
        
        log.info("\n" + "=" * 60)
        log.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
        log.info("=" * 60)
        
    except Exception as e:
        log.error(f"\n❌ Pipeline failed: {e}")
        raise

def validate_setup():
    print("\n🔍 Validating LivItUpDeals Setup...\n")
    errors = []
    warnings = []
    
    # Check Python packages
    print("📦 Checking Python dependencies...")
    required_packages = {
        'dotenv': 'python-dotenv',
        'amazon_paapi': 'python-amazon-paapi',
        'google.generativeai': 'google-generativeai',
        'PIL': 'Pillow',
        'requests': 'requests'
    }
    
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            errors.append(f"Missing package: {package}")
            print(f"  ❌ {package} — Run: pip install {package}")
    
    # Check environment variables
    print("\n🔑 Checking API credentials...")
    required_env = [
        ('AMAZON_ACCESS_KEY', 'Amazon API Access Key'),
        ('AMAZON_SECRET_KEY', 'Amazon API Secret Key'),
        ('AMAZON_ASSOCIATE_TAG', 'Amazon Associate Tag (e.g., yourname-20)'),
        ('GEMINI_API_KEY', 'Google Gemini API Key')
    ]
    
    for key, description in required_env:
        value = os.getenv(key)
        if not value:
            errors.append(f"Missing environment variable: {key}")
            print(f"  ❌ {key} — {description}")
        else:
            masked = value[:8] + '...' if len(value) > 8 else '***'
            print(f"  ✓ {key} = {masked}")
    
    # Check system dependencies
    print("\n🛠️  Checking system dependencies...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print(f"  ✓ FFmpeg installed")
        else:
            errors.append("FFmpeg not working properly")
            print(f"  ❌ FFmpeg not working")
    except FileNotFoundError:
        errors.append("FFmpeg not installed")
        print(f"  ❌ FFmpeg not found — Install from https://ffmpeg.org/")
    except subprocess.TimeoutExpired:
        warnings.append("FFmpeg check timed out")
        print(f"  ⚠️  FFmpeg check timed out")
    
    # Check directory structure
    print("\n📁 Checking directory structure...")
    required_dirs = [VIDEOS_DIR, IMAGES_DIR, LOGS_DIR, DATA_DIR]
    for directory in required_dirs:
        if directory.exists():
            print(f"  ✓ {directory.name}/")
        else:
            print(f"  ⚠️  {directory.name}/ (will be created automatically)")
    
    # Check optional files
    print("\n📄 Checking optional files...")
    music_path = BASE_DIR / "assets" / "background_music.mp3"
    if music_path.exists():
        print(f"  ✓ background_music.mp3")
    else:
        warnings.append("Background music not found (videos will have no audio)")
        print(f"  ⚠️  background_music.mp3 not found")
    
    google_creds = BASE_DIR / "google_credentials" / "client_secret.json"
    if google_creds.exists():
        print(f"  ✓ YouTube OAuth credentials")
    else:
        warnings.append("YouTube credentials not configured (can't upload videos)")
        print(f"  ⚠️  client_secret.json not found (YouTube upload disabled)")
    
    # Summary
    print("\n" + "="*50)
    if errors:
        print(f"❌ {len(errors)} ERROR(S) FOUND:")
        for error in errors:
            print(f"   • {error}")
        print("\nFix these errors before running the pipeline.")
        return False
    elif warnings:
        print(f"⚠️  {len(warnings)} WARNING(S):")
        for warning in warnings:
            print(f"   • {warning}")
        print("\n✅ Setup is valid but some optional features may not work.")
        return True
    else:
        print("✅ All checks passed! You're ready to run the pipeline.")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LivItUpDeals Affiliate Pipeline")
    parser.add_argument("--setup", action="store_true", help="Validate setup")
    parser.add_argument("--run", action="store_true", help="Run the full pipeline")
    parser.add_argument("--update-website", action="store_true", help="Update products.json only (no videos)")
    args = parser.parse_args()
    
    if args.setup:
        validate_setup()
    elif args.run:
        run_pipeline(update_website_only=False)
    elif args.update_website:
        run_pipeline(update_website_only=True)
    else:
        parser.print_help()
