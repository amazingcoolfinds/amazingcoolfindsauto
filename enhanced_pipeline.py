#!/usr/bin/env python3
"""
UPDATED PIPELINE - Absolute Final Version
Fixed typos, Deepseek API key requirement, and restored optimized PRODUCT_TARGETS.
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
        # --- ADAPTIVE SCRAPER ---
        try:
            from core.advanced_scraper import AdvancedScraper
            self.scraper = AdvancedScraper()
            self.search_method_name = None
            for attr in dir(self.scraper):
                if any(word in attr.lower() for word in ["search", "scrape", "fetch"]):
                    self.search_method_name = attr
                    break
        except Exception as e:
            logger.error(f"Scraper unavailable: {e}"); self.scraper = None

        # --- ADAPTIVE GENERATOR (Fixed for DeepseekProductSelector API Key) ---
        try:
            import core.gemini_generators as gg
            self.generator = None
            for attr_name in dir(gg):
                attr = getattr(gg, attr_name)
                if isinstance(attr, type) and any(word in attr_name for word in ["Generator", "Selector", "Product"]):
                    try:
                        # Try initializing with api_key as required by DeepseekProductSelector
                        self.generator = attr(api_key=GEMINI_API_KEY)
                        break
                    except TypeError:
                        try:
                            self.generator = attr()
                            break
                        except: continue
            if not self.generator:
                logger.error("Could not find any valid Generator class in gemini_generators")
        except Exception as e:
            logger.error(f"GeminiGenerator error: {e}"); self.generator = None

        # --- UPLOADERS ---
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

    def get_priority_target_internal(self, products):
        if not PRODUCT_TARGETS: return None
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

    def get_high_performance_products(self, target, min_price=50):
        if not self.scraper or not self.search_method_name:
            logger.error("Scraper or search method not found.")
            return []
        try:
            logger.info(f"🔍 Searching for {target['category']} (min ${min_price}) using {self.search_method_name}...")
            method = getattr(self.scraper, self.search_method_name)
            search_results = method(target['keywords'], max_results=10)
            if not search_results: return []
            existing_ids = {p.get("asin") for p in self.load_existing_products()}
            return [p for p in search_results if p.get("asin") not in existing_ids and float(re.sub(r'[^\d.]', '', p.get("price", "0"))) >= min_price]
        except Exception as e:
            logger.error(f"Error in dynamic search: {e}"); return []

    def run_production_cycle(self):
        logger.info("🚀 STARTING FINAL VERIFIED PIPELINE...")
        logger.info("============================================================")
        
        existing_products = self.load_existing_products()
        priority_target = self.get_priority_target_internal(existing_products)
        if not priority_target:
            logger.error("No targets found."); sys.exit(1)

        logger.info(f"🎯 Target Nicho: {priority_target['category']}")

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
            logger.error("❌ No strategic products found today."); sys.exit(1)

        if not self.generator:
            logger.error("AI Generator unavailable."); sys.exit(1)

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
