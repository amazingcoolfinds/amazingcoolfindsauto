#!/usr/bin/env python3
import os
import sys
import json
import logging
import time
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── SETUP ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("SingleProductTest")

# ─── TEST LOGIC ───────────────────────────────────────────────────
def run_single_product_test():
    log.info("🚀 STARTING SINGLE PRODUCT PIPELINE TEST")
    log.info("=" * 60)

    try:
        from advanced_scraper import AdvancedScraper
        from groq_generators import GroqProductSelector, GroqScriptGenerator, GroqVoiceGenerator
        from video_generator import VideoGenerator
        from enhanced_pipeline import get_enhanced_website_link, save_processed_product, update_website_data
        
        scraper = AdvancedScraper()
        selector = GroqProductSelector(os.getenv("GROQ_API_KEY"))
        gpt_gen = GroqScriptGenerator(os.getenv("GROQ_API_KEY"))
        voice_gen = GroqVoiceGenerator(os.getenv("GROQ_API_KEY"))
        video_gen = VideoGenerator()

        # Step 1: Discovery (Scrape 1 product)
        log.info("🎯 STEP 1: Discovery & Scraping...")
        search_results = scraper.search("premium tech gadgets 2026", max_results=1)
        if not search_results:
            log.error("❌ Search failed")
            return
        
        asin = search_results[0]['asin']
        log.info(f"✅ Found ASIN: {asin}")
        
        log.info(f"🕸️  Scraping details for {asin}...")
        product = scraper.get_details(asin)
        if not product:
            log.error("❌ Details extraction failed")
            return
        
        # Add category and commission for AI analysis
        product['category'] = "Tech"
        product['commission'] = 0.04
        product['website_link'] = get_enhanced_website_link(product)
        product['processed_at'] = datetime.now().isoformat()

        # Step 2: AI Analysis
        log.info("🧠 STEP 2: AI Selection & Scripting...")
        selections = selector.analyze_candidates("Tech", [product])
        if not selections:
            log.warning("⚠️ AI did not select the product, but we will proceed for testing purposes.")
            product['selection_score'] = 85 # Manual override for testing
            product['selection_reasoning'] = "Test product selection."
        else:
            product = selections[0] # Use AI enhanced product

        script = gpt_gen.generate_script(product)
        log.info(f"🎤 Script generated: {script['title']}")

        # Step 3: Media Generation
        log.info("🎥 STEP 3: Media Generation (Voice & Video)...")
        voice_path = voice_gen.generate(script['narration'], product['asin'])
        if not voice_path:
            log.error("❌ Voice generation failed")
            return
            
        video_path = video_gen.generate(product, script, voice_path=voice_path)
        if not video_path:
            log.error("❌ Video generation failed")
            return
        log.info(f"✅ Video created at: {video_path}")

        # Step 4: Uploader Verification (Initialization only to avoid unwanted posts if needed)
        log.info("📡 STEP 4: Uploader Connectivity...")
        from meta_uploader import MetaUploader
        from tiktok_uploader import TikTokUploader
        
        meta = MetaUploader()
        log.info(f"Meta: {'Connected' if meta.access_token else 'Missing Token'}")
        
        tiktok = TikTokUploader()
        log.info(f"TikTok: {'Connected' if tiktok.access_token else 'Missing Token'}")

        # Note: YouTube skipped in this summary script to avoid complex OAuth redirection in dry-run
        
        # Step 5: Sync
        log.info("🌐 STEP 5: Website Sync...")
        save_processed_product(product)
        # update_website_data([product]) # Commented out to not overwrite local data files during a test
        log.info("✅ Mock sync complete (save_processed_product called)")

        log.info("=" * 60)
        log.info("🎉 TEST COMPLETED SUCCESSFULLY!")

    except Exception as e:
        log.exception(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    run_single_product_test()
