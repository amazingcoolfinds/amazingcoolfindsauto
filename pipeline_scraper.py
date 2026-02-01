#!/usr/bin/env python3
"""
Live It Up Deals - Pipeline usando Scraper
"""
import os
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'logs/pipeline_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Directories
BASE_DIR = Path(__file__).parent
VIDEOS_DIR = BASE_DIR / "output_videos"
IMAGES_DIR = BASE_DIR / "output_images"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# BASE URL for the web (change this to your production domain later)
BASE_WEBSITE_URL = "http://localhost:8000"

for directory in [VIDEOS_DIR, IMAGES_DIR, LOGS_DIR, DATA_DIR]:
    directory.mkdir(exist_ok=True)

# ─── PRODUCT TARGETS ────────────────────────────────────────
PRODUCT_TARGETS = [
    {"category": "Beauty", "keywords": "luxury beauty skincare premium", "commission": "10%"},
    {"category": "Beauty", "keywords": "luxury perfume fragrance high end", "commission": "10%"},
    {"category": "Electronics", "keywords": "premium tech gadgets 2025", "commission": "4%"},
    {"category": "Clothing", "keywords": "luxury fashion men premium jacket", "commission": "4%"},
    {"category": "Clothing", "keywords": "luxury fashion women premium dress", "commission": "4%"},
    {"category": "Home", "keywords": "premium home decor luxury modern", "commission": "4%"},
    {"category": "Electronics", "keywords": "premium laptop high end 2025", "commission": "4%"},
    {"category": "Electronics", "keywords": "luxury smartwatch premium 2025", "commission": "4%"},
]

# ─── AMAZON FETCHER (HYBRID: RAPIDAPI + SCRAPER) ──────────────
class AmazonFetcher:
    def __init__(self):
        self.associate_tag = os.getenv("AMAZON_ASSOCIATE_TAG")
        if not self.associate_tag:
            raise EnvironmentError("Missing AMAZON_ASSOCIATE_TAG in .env")
        
        # Initialize fetchers
        from rapidapi_fetcher import AmazonRapidAPI
        from amazon_scraper import AmazonScraper
        
        self.rapidapi = AmazonRapidAPI()
        self.scraper = AmazonScraper(self.associate_tag)
    
    def search(self, keywords: str, count: int = 3) -> list[dict]:
        """Hybrid search: Try RapidAPI, fallback to Scraper"""
        # 1. Try RapidAPI
        products = self.rapidapi.search(keywords, count=count)
        if products:
            log.info(f"✨ Products fetched via RapidAPI for '{keywords}'")
            return products
            
        # 2. Fallback to Scraper (which has its own final fallback)
        log.warning(f"⚠️ RapidAPI failed or empty, falling back to Scraper for '{keywords}'")
        return self.scraper.search(keywords, max_results=count)


# ─── SCRIPT GENERATOR ────────────────────────────────────────
import google.generativeai as gemini

class ScriptGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("Missing GEMINI_API_KEY in .env")
        gemini.configure(api_key=self.api_key)
        self.model = gemini.GenerativeModel('gemini-flash-latest')

    def generate(self, product: dict) -> dict:
        try:
            bullets_text = "\n".join(product.get('bullets', []))[:500]
            prompt = f"""
You are a viral luxury content creator. Write a high-converting narration script for a 15-second product Short.
Focus on lifestyle, status, and the specific benefits below.

Product: {product['title']}
Price: {product['price']}
Key Benefits:
{bullets_text}

Return ONLY valid JSON with these exact keys:
{{
  "title": "Viral YouTube title",
  "narration": "Narration script (EXACTLY 38 words) ending with: 'Link is in the first comment!'. ENGLISH ONLY.",
  "hashtags": ["tag1", "tag2", "tag3"]
}}
"""
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1].rsplit('\n```', 1)[0]
            script = json.loads(raw)
            log.info(f"✓ Professional script generated: {script['title']}")
            return script
        except Exception as e:
            log.error(f"Script generation failed: {e}")
            return {
                "title": f"Viral Deal: {product['title'][:30]}",
                "narration": f"The {product['title'][:50]} is the ultimate lifestyle upgrade you have been waiting for. Experience premium quality, unmatched performance, and a status boost today. Do not wait, get yours now. Link is in the first comment!",
                "hashtags": ["deals", "amazon", "luxury"]
            }


# ─── PIPELINE ─────────────────────────────────────────────────
def run_pipeline(update_website_only=False):
    log.info("=" * 60)
    log.info("🚀 LIVEITUPDEALS PIPELINE STARTED")
    log.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"   Mode: {'Website Update Only' if update_website_only else 'Full Pipeline'}")
    log.info("=" * 60)
    
    try:
        amazon = AmazonFetcher()
        scripts = ScriptGenerator()
        from video_generator import VideoGenerator
        videos = VideoGenerator()
        
        all_products = []
        
        for target in PRODUCT_TARGETS:
            log.info(f"\n🔍 Searching {target['category']}: {target['keywords']}")
            products = amazon.search(
                keywords=target['keywords'],
                count=3
            )
            
            for product in products:
                product['category'] = target['category']
                product['commission'] = target['commission']
                all_products.append(product)
                
                if not update_website_only:
                    script = scripts.generate(product)
                    log.info(f"  Script: {script['title']}")
                    
                    # 1. Generate Voiceover
                    from voice_generator import VoiceGenerator
                    voice_gen = VoiceGenerator()
                    voice_path = voice_gen.generate(script['narration'], product['asin'])
                    
                    if not voice_path:
                        log.error(f"❌ Critical Error: Could not generate voiceover for {product['asin']}. Stopping to avoid silent video.")
                        raise RuntimeError(f"Voiceover generation failed for {product['asin']}. Check API quotas.")
                    
                    # 2. Generate Carousel Video
                    video_path = videos.generate(product, script, voice_path=voice_path)
                    
                    if video_path:
                        product['video_path'] = str(video_path)
                        
                        # 3. Automatic YouTube Upload
                        try:
                            from youtube_uploader import YouTubeUploader
                            uploader = YouTubeUploader()
                            
                            # Construct video link for description
                            web_link = f"{BASE_WEBSITE_URL}/#{product['asin']}"
                            description = f"{script['narration']}\n\n🔥 Get it here: {web_link}\n\n#amazondeals #luxury #shopping"
                            
                            log.info(f"📤 Starting YouTube upload for {product['asin']}...")
                            yt_url = uploader.upload_short(
                                video_path=video_path,
                                title=script['title'],
                                description=description,
                                tags=script['hashtags']
                            )
                            if yt_url:
                                product['youtube_url'] = yt_url
                                log.info(f"✅ Product updated with YouTube URL: {yt_url}")
                        except Exception as e:
                            log.error(f"❌ YouTube upload failed for {product['asin']}: {e}")
                            # We continue even if upload fails to keep the product in list
            
            time.sleep(0.5) 
        
        # Save to JSON
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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LivItUpDeals Pipeline")
    parser.add_argument("--update-website", action="store_true", help="Update products.json only")
    args = parser.parse_args()
    
    if args.update_website:
        run_pipeline(update_website_only=True)
    else:
        run_pipeline(update_website_only=False)
