#!/usr/bin/env python3
"""
FINAL SYNCHRONIZED PIPELINE - Version 1.1 (Cleaned)
Fixed syntax error 'min_//price' and maintained optimized niche targets.
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

# ─── CONFIGURATION ──────────────────────────────────────────
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
        # 1. Load Scraper - Verified Exact Name
        try:
            from core.advanced_scraper import AdvancedScraper
            self.scraper = AdvancedScraper()
            logger.info("✅ AdvancedScraper loaded")
        except Exception as e:
            logger.error(f"❌ Scraper load failed: {e}"); self.scraper = None

        # 2. Load Generator - Verified Exact Name
        try:
            from core.gemini_generators import GeminiGenerator
            self.generator = GeminiGenerator(api_key=GEMINI_API_KEY)
            logger.info("✅ GeminiGenerator loaded")
        except Exception as e:
            logger.error(f"❌ Generator load failed: {e}"); self.generator = None

        # 3. Uploaders (Tolerant)
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
        if not PRODUCT_TARGETS: return None
        
        category_map = {
            "Tech": "Elite Tech",
            "Life & Style": "Beauty & Glow",
            "Home & Auto": "Smart Home",
            "Clothing": "Quiet Luxury"
        }
        
        counts = {}
        for p in products:
            cat = p.get("category", "Unknown")
            mapped_cat = category_map.get(cat, cat)
            counts[mapped_cat] = counts.get(mapped_cat, 0) + 1
        
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
        if not self.scraper: return []
        try:
            logger.info(f"🔍 Searching for {target['category']} (min ${min_price})...")
            results = self.scraper.scrape_amazon_products(target['keywords'], max_//results=10)
            # FIXED: Corrected search call
            results = self.scraper.scrape_amazon_products(target['keywords'], max_results=10)
            if not results: return []
            existing_ids = {p.get("asin") for p in self.load_existing_products()}
            return [p for p in results if p.get("asin") not in existing_ids and float(re.sub(r'[^\d.]', '', p.get("price", "0"))) >= min_price]
        except Exception as e:
            logger.error(f"Search error: {e}"); return []

    def run_production_cycle(self):
        logger.info("🚀 STARTING SYNCHRONIZED STABILITY PIPELINE...")
        logger.info("============================================================")
        
        if not self.scraper or not self.generator:
            logger.error("❌ Essential modules (Scraper or AI) missing. Aborting."); sys.exit(1)

        existing_products = self.load_existing_products()
        target = self.get_priority_target(existing_products)
        if not target:
            logger.error("No targets found."); sys.exit(1)

        logger.info(f"🎯 Target Nicho: {target['category']}")

        thresholds = [50, 35, 20]
        found_anything = False
        new_discoveries = []
        
        for threshold in thresholds:
            # FIXED: removed any // or typos here
            products = self.get_high_performance_products(target, min_price=threshold)
            if products:
                new_discoveries.extend(products)
                found_anything = True
                break
        
        if not found_anything:
            logger.error("❌ No strategic products found today."); sys.exit(1)

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
