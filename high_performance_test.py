#!/usr/bin/env python3
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("SelectionTest")

# Load env
load_dotenv()

def test_selection_logic():
    try:
        from enhanced_pipeline import get_high_performance_products
        
        log.info("🚀 Starting High-Performance Selection Test...")
        log.info("Selecting top products from 5 candidates (for speed)...")
        
        # Test with 5 candidates
        selections = get_high_performance_products(count_candidates=5, select_top=2)
        
        if selections:
            log.info(f"✅ SUCCESSFULLY SELECTED {len(selections)} PRODUCTS")
            for i, p in enumerate(selections, 1):
                log.info(f"--- Selection #{i} ---")
                log.info(f"ASIN: {p['asin']}")
                log.info(f"Title: {p['title'][:60]}...")
                log.info(f"Score: {p.get('selection_score')}")
                log.info(f"Reasoning: {p.get('selection_reasoning')}")
                log.info(f"BSR: {p.get('bsr')}")
                log.info(f"Prime: {p.get('is_prime')}")
                log.info(f"Website Link: {p['website_link']['link']}")
        else:
            log.warning("⚠️ No products met the criteria (Score >= 70).")
            # If no products were selected, let's at least see if any were FOUND
            # In a real run, we'd log them to a separate file for analysis.
            
    except Exception as e:
        log.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_selection_logic()
