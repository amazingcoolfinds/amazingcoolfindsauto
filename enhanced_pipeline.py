#!/usr/bin/env python3
"""
UPDATED PIPELINE - Final stability version
Corrected class names to match core modules and robust config loading.
"""

import logging
import time
import re
import random
import json
import sys
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
        print("❌ CRITICAL ERROR: Could not find config.py in the project root.")
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

# Internal Module Imports
from core.advanced_scraper import AdvancedScraper
from core.gemini_generators import GeminiGenerator # FIXED: Corrected name
from core.meta_uploader import MetaUploader
from core.tiktok_uploader import TikTokUploader
from core.youtube_uploader import YouTubeUploader
from core.strategy_monitor import StrategyMonitor

# Logging Configuration
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
        self.scraper = AdvancedScraper()
        self.generator = GeminiGenerator() # FIXED: Corrected name
        self.strategy = StrategyMonitor()
        self.yt_uploader = YouTubeUploader()
        self.tt_uploader = TikTokUploader()
        self.meta_uploader = MetaUploader()

    def load_existing_products(self):
        if not PRODUCTS_JSON.exists():
            return []
        try:
            with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_products(self, products):
        with open(PRODUCTS_JSON, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=4, ensure_ascii=False)

    def get_high_performance_products(self, target, min_price=50):
        try:
            logger.info(f"🔍 Searching for {target['category']} products (min ${min_price})...")
            search_results = self.scraper.fetch_amazon_products(
                target['keywords'], 
                max_results=10
            )
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
            logger.error(f"Error in high-performance selection: {e}")
            return []

    def run_production_cycle(self):
        logger.info("🚀 STARTING ENHANCED AUTOMATED PIPELINE...")
        logger.info("============================================================")
        
        existing_products = self.load_existing_products()
        new_discoveries = []
        
        priority_target = self.strategy.get_priority_target(existing_products)
        if not priority_target:
            logger.error("Could not determine priority target.")
            return

        thresholds = [50, 35, 20]
        found_anything = False
        
        for threshold in thresholds:
            products = self.get_high_performance_products(priority_target, min_price=threshold)
            if products:
                new_discoveries.extend(products)
                found_anything = True
                break
        
        if not found_anything:
            logger.error("❌ No strategic products found today after all attempts.")
            sys.exit(1)

        for prod in new_discoveries[:MAX_UPLOADS_PER_RUN]:
            try:
                # The generate_marketing_assets method remains the same in GeminiGenerator
                enriched_data = self.generator.generate_marketing_assets(prod)
                self.yt_uploader.upload(enriched_data)
                self.tt_uploader.upload(enriched_data)
                self.meta_uploader.upload(enriched_data)
                
                existing_products.append(prod)
                self.save_products(existing_products)
                
                logger.info(f"✅ Successfully processed and uploaded: {prod.get('title')}")
            except Exception as e:
                logger.error(f"Failed to process product {prod.get('asin')}: {e}")

        logger.info("🏁 Pipeline cycle completed successfully.")

if __name__ == "__main__":
    pipeline = EnhancedPipeline()
    pipeline.run_production_cycle()
