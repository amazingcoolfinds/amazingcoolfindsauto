#!/usr/bin/env python3
"""
UPDATED PIPELINE - Final Stability & Compatibility Version
Fixes StrategyMonitor arguments and adds extreme tolerance to module imports.
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
        # 1. Advanced Scraper
        try:
            from core.advanced_scraper import AdvancedScraper
            self.scraper = AdvancedScraper()
        except Exception as e:
            logger.error(f"Failed to load AdvancedScraper: {e}")
            self.scraper = None

        # 2. Gemini Generator (Dynamic attempt)
        try:
            from core import gemini_generators
            # Try to find the class regardless of the name (GeminiGenerator or GeminiProductGenerator)
            self.generator = getattr(gemini_generators, "GeminiGenerator", 
                        getattr(gemini_generators, "GeminiProductGenerator", None))()
        except Exception as e:
            logger.error(f"Failed to load GeminiGenerator: {e}")
            self.generator = None

        # 3. Strategy Monitor (FIXED: Added DATA_DIR argument)
        try:
            from core.strategy_monitor import StrategyMonitor
            self.strategy = StrategyMonitor(DATA_DIR)
        except Exception as e:
            logger.error(f"Failed to load StrategyMonitor: {e}")
            self.strategy = None

        # 4. Uploaders (Tolerant loading)
        try:
            from core.youtube_uploader import YouTubeUploader
            self.yt_uploader = YouTubeUploader()
        except Exception as e:
            logger.error(f"YouTubeUploader unavailable: {e}")
            self.yt_uploader = None

        try:
            from core.tiktok_uploader import TikTokUploader
            self.tt_uploader = TikTokUploader()
        except Exception as e:
            logger.error(f"TikTokUploader unavailable: {e}")
            self.tt_uploader = None

        try:
            from core.meta_uploader import MetaUploader
            self.meta_uploader = MetaUploader()
        except Exception as e:
            logger.error(f"MetaUploader unavailable: {e}")
            self.meta_uploader = None

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
        if not self.scraper:
            logger.error("Scraper not available.")
            return []
        try:
            logger.info(f"🔍 Searching for {target['category']} products (min ${min_price})...")
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
            logger.error(f"Error in high-performance selection: {e}")
            return []

    def run_production_cycle(self):
        logger.info("🚀 STARTING ENHANCED AUTOMATED PIPELINE...")
        logger.info("============================================================")
        
        if not self.strategy:
            logger.error("Strategy Monitor not available. Aborting.")
            sys.exit(1)

        existing_products = self.load_existing_products()
        priority_target = self.strategy.get_priority_target(existing_products)
        if not priority_target:
            logger.error("Could not determine priority target.")
            return

        thresholds = [50, 35, 20]
        found_anything = False
        new_discoveries = []
        
        for threshold in thresholds:
            products = self.get_high_performance_products(priority_target, min_price=threshold)
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
