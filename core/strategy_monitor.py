#!/usr/bin/env python3
"""
Strategy Monitor - Strategic product discovery and profit optimization
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
import random

log = logging.getLogger("StrategyMonitor")

class StrategyMonitor:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.products_file = data_dir / "products.json"
        # Commission rates by category
        self.commissions = {
            "Tech": 0.04,
            "Lifestyle": 0.10,
            "Home": 0.03,
            "Auto": 0.04,
            "Electronics": 0.04,
            "Beauty": 0.10,
            "Toys": 0.03
        }

    def get_discovery_priority(self):
        """
        Analyzes the current product database and returns targets prioritized 
        by which category has fewer items to ensure balanced growth.
        """
        counts = {"Tech": 0, "Lifestyle": 0, "Home": 0, "Auto": 0}
        
        # Load current product counts
        if self.products_file.exists():
            try:
                with open(self.products_file, 'r') as f:
                    products = json.load(f)
                    for p in products:
                        cat = p.get('category')
                        if cat in counts:
                            counts[cat] += 1
            except Exception as e:
                log.warning(f"Error counting products for balance: {e}")

        # Define high-intent, targeted keywords for realistic Amazon searches
        lifestyle_keywords = ["luxury skincare set", "premium espresso machine maker", "shiatsu massage gun", "designer sunglasses polarized", "high end blender smoothie"]
        tech_keywords = ["4k gaming monitor", "premium mechanical keyboard OLED", "smart noise cancelling headphones", "VR headset advanced", "portable power station 1000w"]
        home_keywords = ["smart air purifier HEPA", "robot vacuum mop combo", "luxury automated curtains", "premium memory foam mattress topper", "smart security camera system 4k"]
        auto_keywords = ["4k dual dash cam", "portable car jump starter 2000A", "wireless apple carplay adapter", "premium car detailing kit professional", "portable tire inflator air compressor digital"]

        # Mix the targets
        targets = [
            {"category": "Lifestyle", "keywords": random.choice(lifestyle_keywords), "count": counts["Lifestyle"]},
            {"category": "Tech", "keywords": random.choice(tech_keywords), "count": counts["Tech"]},
            {"category": "Home", "keywords": random.choice(home_keywords), "count": counts["Home"]},
            {"category": "Auto", "keywords": random.choice(auto_keywords), "count": counts["Auto"]}
        ]

        # Sort by count (ascending) to prioritize the least populated category
        targets.sort(key=lambda x: x['count'])
        
        log.info(f"📊 Category Balance: {counts}")
        log.info(f"🎯 Priority Target: {targets[0]['category']} ({targets[0]['count']} items)")
        
        return targets

    def calculate_potential_profit(self, price_str: str, category: str):
        """Calculates estimated commission in USD"""
        try:
            # Clean price string: "$39.99" -> 39.99
            price = float(price_str.replace('$', '').replace(',', ''))
            rate = self.commissions.get(category, 0.04)
            return price * rate
        except:
            return 0.0

    def analyze_weekly_kpis(self):
        """Analyzes which categories/price points are performing best (Simulated)"""
        log.info("📈 Analyzing weekly performance trends...")
        return {
            "top_category": "Lifestyle",
            "avg_commission": "$5.42",
            "best_price_range": "$100 - $300"
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = StrategyMonitor(Path("./data"))
    print("Strategic Targets:", monitor.get_discovery_priority())
    print("Profit Test (Lifestyle, $50):", monitor.calculate_potential_profit("$50", "Lifestyle"))
