#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          AMAZING COOL FINDS — 100% AUTOMATED PIPELINE           ║
║   Amazon → AI Script → Video → YT / TT / FB / IG / Pinterest    ║
║        Web Synchronizer & Cloudflare Automation Included        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── PATHS ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
AMAZING_DATA_DIR = BASE_DIR / "amazing" / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

for d in [LOGS_DIR, DATA_DIR, AMAZING_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── ENV & LOGGING ───────────────────────────────────────────────
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
    {"category": "Home", "keywords": "smart home devices 2026", "commission": "4%"},
]

# ─── RECOVERY & AUTOMATION HELPERS ─────────────────────────────────
def get_website_link(product):
    """Generates enhanced website link with unique ID and smooth scroll."""
    import hashlib
    import time
    
    base_url = os.getenv("WEBSITE_URL", "https://amazing-cool-finds.com")
    
    # Generate unique ID
    timestamp = str(int(time.time()))
    unique_string = f"{product['asin']}-{timestamp}"
    unique_id = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    # Direct link to product card (Static safe)
    enhanced_link = f"{base_url}/index.html#{product['asin']}"
    
    return enhanced_link

def send_to_make(product):
    """Sends product data to Make.com for Reddit review automation."""
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")
    if not webhook_url or "your_webhook" in webhook_url:
        log.warning("⚠️ Make.com Webhook URL not configured. Skipping.")
        return
    
    try:
        log.info(f"⚡ Sending {product['asin']} to Make.com...")
        response = requests.post(webhook_url, json=product, timeout=10)
        if response.ok:
            log.info("✓ Webhook sent successfully.")
        else:
            log.error(f"❌ Webhook failed: {response.status_code}")
    except Exception as e:
        log.error(f"❌ Webhook error: {e}")

def deploy_to_site():
    """Automates Cloudflare Pages deployment for the 'amazing/' folder."""
    project_name = os.getenv("CF_PROJECT_NAME", "amazing-cool-finds")
    log.info(f"☁️  Deploying 'amazing/' folder to Cloudflare project: {project_name}...")
    
    try:
        cmd = ["npx", "wrangler", "pages", "deploy", "amazing/", "--project-name", project_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log.info("🚀 Deployment SUCCESSFUL!")
        else:
            log.error(f"❌ Deployment FAILED: {result.stderr}")
    except Exception as e:
        log.error(f"❌ Deployment error: {e}")

# ─── UNIFIED FETCHER ─────────────────────────────────────────────
class AmazonFetcher:
    def __init__(self):
        self.associate_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "amazingcoolfinds-20")
        
        # Core Components - AI Script Generator (Groq)
        try: 
            from groq_generators import GroqScriptGenerator
            GROQ_KEY = os.environ.get("GROQ_API_KEY")
            self.script_gen = GroqScriptGenerator(GROQ_KEY) if GROQ_KEY else None
            if self.script_gen:
                log.info("✅ Groq Script Generator initialized")
        except ImportError:
            log.error("Groq script generator not found.")
            self.script_gen = None
        
        # Groq Voice Generator
        try: 
            from groq_generators import GroqVoiceGenerator
            GROQ_KEY = os.environ.get("GROQ_API_KEY")
            self.voice_gen = GroqVoiceGenerator(GROQ_KEY) if GROQ_KEY else None
        except ImportError:
            log.error("Groq voice generator not found.")
            self.voice_gen = None
            
        try: 
            from video_generator import VideoGenerator
            self.video_gen = VideoGenerator()
        except ImportError:
            self.video_gen = None
        
        # Core Components - Working Scraper from skills
        import sys
        skills_scraper_path = str(BASE_DIR / ".agent" / "skills" / "amazon-scraper" / "scripts")
        if skills_scraper_path not in sys.path:
            sys.path.append(skills_scraper_path)
        
        try:
            from amazon_scraper_lib import AmazonScraper
            self.scraper = AmazonScraper(self.associate_tag)
        except ImportError:
            log.error("Working AmazonScraper not found in skills.")
            self.scraper = None
        
    def search(self, keywords: str, count: int = 3) -> list:
        if self.scraper:
            log.info(f"🔍 Discovery: Using working scraper for '{keywords}'...")
            return self.scraper.search(keywords, max_results=count)
        return []

    def process_product(self, product: dict):
        asin = product['asin']
        log.info(f"Processing {asin}: {product['title'][:30]}...")
        
        # 1. Enrich Product Data (Hi-res images, real price, bullets)
        details = self.scraper.get_details(asin) if self.scraper else None
        
        # Merge safely: Don't overwrite good search titles with None/empty from scraper
        enriched_product = product.copy()
        if details:
            # Only update keys that have meaningful values
            for key, val in details.items():
                if val: # Skip None, empty lists, or empty strings
                    enriched_product[key] = val
        else:
            log.warning(f"⚠️  Could not enrich {asin}. Using search data.")
        
        # 2. Generate Script (Smart Generator)
        script = self.script_gen.generate_script(enriched_product) if self.script_gen else None
        if not script: return None, None, enriched_product
        
        # 3. Generate Voiceover (Groq)
        voice_path = self.voice_gen.generate(script['narration'], asin) if self.voice_gen else None
        if not voice_path: return None, None, enriched_product
        
        # 4. Create Video (FFmpeg)
        video_path = self.video_gen.generate(enriched_product, script, voice_path=voice_path) if self.video_gen else None
            
        return video_path, script, enriched_product

# ─── MAIN PIPELINE ───────────────────────────────────────────────
def run_pipeline():
    log.info("🚀 PIPELINE STARTED (Web Sync & Quality Engine)")
    
    try:
        fetcher = AmazonFetcher()
        from youtube_production import ProductionYouTubeUploader
        from meta_uploader import MetaUploader
        from tiktok_uploader import TikTokUploader
        
        try: yt_up = ProductionYouTubeUploader()
        except: yt_up = None
        
        try: meta_up = MetaUploader()
        except: meta_up = None
        
        try: tt_up = TikTokUploader()
        except: tt_up = None
        
        # Load existing products to avoid losing history
        all_products = []
        if AMAZING_DATA_DIR.joinpath("products.json").exists():
            try:
                with open(AMAZING_DATA_DIR / "products.json", 'r') as f:
                    all_products = json.load(f)
            except: pass
        
        newly_processed = []

        for target in PRODUCT_TARGETS:
            log.info(f"--- Category: {target['category']} ---")
            products = fetcher.search(target['keywords'], count=1)
            
            for product in products:
                # Basic enrichment
                product['category'] = target['category']
                product['commission'] = target['commission']
                
                # Full video process and detailed extraction
                res = fetcher.process_product(product)
                if res:
                    video_path, script, enriched_product = res
                    # Prioritize the enriched data for the database
                    product = enriched_product
                    
                    # 🔗 Generate and attach the internal website link
                    product['website_link'] = get_website_link(product)

                    # Only proceed if video was successfully created
                    if video_path and script:
                        # ⚡ Automation: Send to Make.com only when video is ready
                        send_to_make(product)
                        log.info(f"🔗 Social Media Link: {product['website_link']}")
                        
                        desc = f"{script['narration']}\n\n🔥 Get it here: {product['website_link']}\n\n" + " ".join(script.get('hashtags', []))
                        
                        # Uploads
                        if yt_up: 
                            # Pass affiliate_url for the first comment
                            yt_up.upload_video(video_path, script['title'], desc, script.get('hashtags', []), product.get('affiliate_url'))
                        if meta_up:
                            meta_up.upload_to_facebook(video_path, f"{script['title']}\n{desc}")
                            meta_up.upload_to_instagram(video_path, f"{script['title']}\n{desc}")
                        if tt_up: tt_up.upload_video(video_path, script['title'])
                        
                # Sync into the historical database
                # Avoid duplicates
                if not any(p['asin'] == product['asin'] for p in all_products):
                    all_products.insert(0, product) # LATEST FIRST
                    newly_processed.append(product)
            
        # 📂 Dual Directory Sync
        for path in [DATA_DIR / "products.json", AMAZING_DATA_DIR / "products.json"]:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, indent=2)
            log.info(f"✓ Data synchronized to {path}")

        # 🚀 Deploy the 'amazing' folder only
        if newly_processed:
            deploy_to_site()
        else:
            log.info("No new products to deploy.")
            
        log.info("✅ Pipeline Execution Finished")
        
    except Exception as e:
        log.error(f"Pipeline Failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.run: run_pipeline()
    else: parser.print_help()
