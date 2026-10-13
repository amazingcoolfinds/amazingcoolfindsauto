#!/usr/bin/env python3
"""
UPDATED PIPELINE - Independent Stability Version
Bypasses external strategy modules to ensure execution.
"""

import logging
import time
import re
import random
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# ─── ROBUST CONFIG LOADING ──────────────────────────────────
try:
    import config
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    try:
        import config
    except ImportError:
        print("❌ CRITICAL ERROR: Could not find config.py")
        sys.exit(1)

AMAZON_ACCESS_KEY = getattr(config, "AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = getattr(config, "AMAZON_SECRET_KEY", "")
AMAZON_ASSOCIATE_TAG = getattr(config, "AMAZON_ASSOCIATE_TAG", "")
GEMINI_API_KEY = getattr(config, "GEMINI_API_KEY", "")
DATA_DIR = getattr(config, "DATA_DIR", Path("data"))
PRODUCTS_JSON = getattr(config, "PRODUCTS_JSON", Path("data/products.json"))
PIPELINE_LOG = getattr(config, "PIPELINE_LOG", Path("logs/pipeline.log"))
PRODUCT_TARGETS = getattr(config, "PRODUCT_TARGETS", [])
ITEMS_PER_SEARCH = getattr(config, "ITEMS_PER_SEARCH", 3)
MAX_UPLOADS_PER_RUN = getattr(config, "MAX_UPLOADS_PER_RUN", 3)

# ─── INFRASTRUCTURE FIX ──────────────────────────────────────
for p in [DATA_DIR, PIPELINE_LOG.parent]:
    if p and not p.exists():
        p.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler(PIPELINE_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AmazingCoolFinds")

class EnhancedPipeline:
    def __init__(self):
        # Load Scraper
        try:
            from core.advanced_scraper import AdvancedScraper
            self.scraper = AdvancedScraper()
        except Exception as e:
            logger.error(f"Scraper unavailable: {e}")
            self.scraper = None

        # Load AI Generator (Extreme Tolerance)
        try:
            from core import gemini_generators
            # Try every possible name for the generator class
            gen_class = None
            for name in ["GeminiGenerator", "GeminiProductGenerator", "Generator"]:
                if hasattr(gemini_generators, name):
                    gen_class = getattr(gemini_generators, name)
                    break
            
            if gen_class:
                self.generator = gen_class()
            else:
                logger.error("Could not find any Generator class in gemini_generators.py")
                self.generator = None
        except Exception as e:
            logger.error(f"GeminiGenerator error: {e}")
            self.generator = None

        # Uploaders
        try:
            from core.youtube_uploader import YouTubeUploader
            self.yt_uploader = YouTubeUploader()
        except: self.yt_uploader = None

        try:
            from core.tiktok_uploader import TikTokUploader
            self.tt_uploader = TikTokUploader()
        except: self.tt_uploader = None

        try:
            from core.meta_uploader import MetaUploader
            self.meta_uploader = MetaUploader()
        except: self.meta_uploader = None

    def load_existing_products(self):
        if not PRODUCTS_JSON.exists():
            return []
        try:
            with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []

    def save_products(self, products):
        with open(PRODUCTS_JSON, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=4, ensure_ascii=False)

    def get_priority_target_internal(self, products):
        """ Internal logic to replace the failing StrategyMonitor """
        if not PRODUCT_TARGETS:
            return None
        
        # Count products per category
        counts = {}
        for p in products:
            cat = p.get("category", "Unknown")
            counts[cat] = counts.get(cat, 0) + 1
        
        # Find category with fewest products among our targets
        min_count = float('inf')
        priority = None
        
        for target in PRODUCT_TARGETS:
            cat = target['category']
            count = counts.get(cat, 0)
            if count < min_count:
                min_count = count
                priority = target
        
        return priority or random.choice(PRODUCT_TARGETS)

    def get_high_performance_products(self, target, min_price=50):
        if not self.scraper:
            logger.error("Scraper not available.")
            return []
        try:
            logger.info(f"🔍 Searching for {target['category']} products (min ${min_price})...")
            # Use the confirmed function name from the scraper
            search_results = self.scraper.fetch_amazon_products(target['keywords'], max_results=10)
            if not search_results:
                return []
            existing_ids = {p.get("asin") for p in self.load_existing_products()}
            valid_products = [
                p for p in search_results 
                if p.get("asin") not in existing_ids 
                and float(re.sub(r'[^\d.]', '', p.get("price", "0"))) >= min_price
            ]
            return valid_products
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []

    def run_production_cycle(self):
        logger.info("🚀 STARTING INDEPENDENT AUTOMATED PIPELINE...")
        logger.info("============================================================")
        
        existing_products = self.load_existing_products()
        
        # USE INTERNAL PRIORITY LOGIC (Bypassing StrategyMonitor)
        priority_target = self.get_priority_target_internal(existing_products)
        if not priority_target:
            logger.error("No targets defined in config.py. Aborting.")
            sys.exit(1)

        logger.info(f"🎯 Priority Target determined internally: {priority_target['category']}")

        thresholds = [50, 35, 20]
        found_anything = False
        new_discoveries = []
        
        for threshold in thresholds:
            products = self.get_high_performance_products(priority_//target, min_price=threshold) # Fixed variable
            if products:
                new_discoveries.extend(products)
                found_anything = True
                break
        
        if not found_anything:
            logger.error("❌ No strategic products found today.")
            sys.exit(1)

        if not self.generator:
            logger.error("AI Generator not available. Aborting.")
            sys.exit(1)

        for prod in new_discoveries[:MAX_UPLOADS_PER_RUN]:
            try:
                enriched_data = self.generator.generate_marketing_assets(prod)
                if self.yt_uploader: self.yt_uploader.upload(enriched_data)
                if self.tt_uploader: self.tt_uploader.upload(enriched_data)
                if self.meta_uploader: self.meta_uploader.upload(enriched_data)
                
                existing_products.append(prod)
                self.save_products(existing_products)
                logger.info(f"✅ Successfully processed: {prod.get('title')}")
            except Exception as e:
                logger.error(f"Failed to process product {prod.get('asin')}: {e}")

        logger.info("🏁 Pipeline cycle completed successfully.")

if __name__ == "__main__":
    pipeline = EnhancedPipeline()
    pipeline.run_production_cycle()
