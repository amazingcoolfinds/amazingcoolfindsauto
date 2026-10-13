#!/usr/bin/env python3
"""
FINAL STABLE PIPELINE - Optimized Niches & Brute-Force Execution
Strictly matched with AdvancedScraper.scrape_amazon_products and GeminiProductGenerator.
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

# ─── HARDCODED CONFIG (Bypassing config.py for absolute stability) ──────────────────
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "amazingcoolfinds-20")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATA_DIR = Path("data")
PRODUCTS_JSON = DATA_DIR / "products.json"
PIPELINE_LOG = Path("logs/pipeline.log")
ITEMS_PER_SEARCH = 3
MAX_UPLOADS_PER_RUN = 3

# TARGETS OPTIMIZED FOR WEBSITE ORGANIZATION (The "Niches of Desire")
PRODUCT_TARGETS = [
    # --- NICHO: Belleza & Cuidado Premium ---
    {"category": "Beauty & Glow", "keywords": "luxury skincare premium anti-aging", "commission": "10%"},
    {"category": "Beauty & Glow", "keywords": "luxury perfume fragrance niche", "commission": "10%"},

    # --- NICHO: Tecnología Elite & Setup ---
    {"category": "Elite Tech", "keywords": "viral gadgets 2025 trending tech", "commission": "4%"},
    {"category": "Elite Tech", "keywords": "gaming setup accessories premium", "commission": "4%"},
    {"category": "Elite Tech", "keywords": "luxury smartwatch premium 2025", "commission": "4%"},
    {"category": "Elite Tech", "keywords": "premium laptop high end 2025", "commission": "3%"},

    # --- NICHO: Moda Minimalista / Lujo Silencioso ---
    {"category": "Quiet Luxury", "keywords": "luxury fashion men minimal premium", "commission": "4%"},
    {"category": "Quiet Luxury", "keywords": "luxury fashion women elegant premium", "commission": "4%"},

    # --- NICHO: Hogar Inteligente & Moderno ---
    {"category": "Smart Home", "keywords": "premium home decor luxury modern", "commission": "3%"},
    {"category": "Smart Home", "keywords": "smart home gadgets automation premium", "commission": "3%"},
]

# Ensure directories exist
for p in [DATA_DIR, PIPELINE_LOG.parent]:
    if p and not p.exists(): p.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
    handlers=[logging.FileHandler(PIPELINE_LOG), logging.StreamHandler()]
)
logger = logging.getLogger("AmazingCoolFinds")

class EnhancedPipeline:
    def __init__(self):
        # EXPLICIT IMPORTS - No adaptive magic, just direct calls
        try:
            from core.advanced_scraper import AdvancedScraper
            self.scraper = AdvancedScraper()
            logger.info("✅ AdvancedScraper loaded successfully")
        except Exception as e:
            logger.error(f"❌ CRITICAL: AdvancedScraper load failed: {e}")
            self.scraper = None

        try:
            from core.gemini_generators import GeminiProductGenerator
            self.generator = GeminiProductGenerator(api_key=GEMINI_API_KEY)
            logger.info("✅ GeminiProductGenerator loaded successfully")
        except Exception as e:
            logger.error(f"❌ CRITICAL: GeminiProductGenerator load failed: {e}")
            self.generator = None

        # Uploaders (Optional)
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
        if not PRODUCTS_JSON.exists(): return []
        try:
            with open(PRODUCTS_JSON, "r", encoding="utf-8") as f: return json.load(f)
        except: return []

    def save_products(self, products):
        with open(PRODUCTS_JSON, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=4, ensure_ascii=False)

    def get_priority_target(self, products):
        counts = {}
        for p in products:
            cat = p.get("category", "Unknown")
            counts[cat] = counts.get(cat, 0) + 1
        
        min_count = float('inf')
        priority = None
        for target in PRODUCT_TARGETS:
            cat = target['category']
            count = counts.get(cat, 0)
            if count < min_count:
                min_count = count
                priority = target
        return priority or random.choice(PRODUCT_TARGETS)

    def run_production_cycle(self):
        logger.info("🚀 STARTING BRUTE-FORCE PIPELINE WITH OPTIMIZED NICHES...")
        logger.info("============================================================")
        
        if not self.scraper or not self.generator:
            logger.error("❌ Essential modules (Scraper or AI) missing. Aborting.")
            sys.exit(1)

        existing_products = self.load_existing_products()
        target = self.get_priority_target(existing_products)
        logger.info(f"🎯 Target Nicho: {target['category']}")

        # Try search with decreasing price thresholds
        thresholds = [50, 35, 20]
        found_anything = False
        new_discoveries = []
        
        for threshold in thresholds:
            try:
                logger.info(f"🔍 Searching for {target['category']} (min ${threshold})...")
                # EXPLICIT CALL to the verified function name
                results = self.scraper.scrape_amazon_products(target['keywords'], max_results=10)
                if results:
                    existing_ids = {p.get("asin") for p in existing_products}
                    valid = [p for p in results if p.get("asin") not in existing_ids and float(re.sub(r'[^\d.]', '', p.get("price", "0"))) >= threshold]
                    if valid:
                        new_discoveries.extend(valid)
                        found_anything = True
                        break
            except Exception as e:
                logger.error(f"Search error at ${threshold}: {e}")

        if not found_anything:
            logger.error("❌ No products found today."); sys.exit(1)

        # AI Processing & Upload
        for prod in new_discoveries[:MAX_UPLOADS_PER_RUN]:
            try:
                enriched_data = self.generator.generate_marketing_assets(prod)
                if self.yt_uploader: self.yt_uploader.upload(enriched_data)
                if self.tt_uploader: self.tt_uploader.upload(enriched_data)
                if self.meta_uploader: self.meta_uploader.upload(enriched_data)
                existing_products.append(prod)
                self.save_products(existing_products)
                logger.info(f"✅ Processed: {prod.get('title')}")
            except Exception as e:
                logger.error(f"Failed product {prod.get('asin')}: {e}")

        logger.info("🏁 Pipeline completed successfully.")

if __name__ == "__main__":
    pipeline = EnhancedPipeline()
    pipeline.run_production_cycle()
