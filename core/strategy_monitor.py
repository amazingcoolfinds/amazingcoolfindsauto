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
            "Beauty & Glow": 0.10,
            "Elite Tech": 0.04,
            "Quiet Luxury": 0.04,
            "Smart Home": 0.03,
        }

    def get_discovery_priority(self):
        """
        Analyzes the current product database and returns targets prioritized 
        by which category has fewer items to ensure balanced growth.
        """
        counts = {
            "Beauty & Glow": 0,
            "Elite Tech": 0,
            "Quiet Luxury": 0,
            "Smart Home": 0,
        }
        legacy_category_map = {
            "Beauty": "Beauty & Glow",
            "Life & Style": "Beauty & Glow",
            "Clothing": "Quiet Luxury",
            "Electronics": "Elite Tech",
            "Tech": "Elite Tech",
            "Home": "Smart Home",
            "Home & Auto": "Smart Home",
        }
        
        # Load current product counts
        if self.products_file.exists():
            try:
                with open(self.products_file, 'r') as f:
                    products = json.load(f)
                    for p in products:
                        cat = legacy_category_map.get(p.get('category'), p.get('category'))
                        if cat in counts:
                            counts[cat] += 1
            except Exception as e:
                log.warning(f"Error counting products for balance: {e}")

        # Define high-intent, targeted keywords for realistic Amazon searches
        beauty_keywords = [
            "luxury skincare premium anti-aging",
            "luxury perfume fragrance niche",
        ]
        tech_keywords = [
            "viral gadgets 2025 trending tech",
            "gaming setup accessories premium",
            "luxury smartwatch premium 2025",
            "premium laptop high end 2025",
        ]
        luxury_keywords = [
            "luxury fashion men minimal premium",
            "luxury fashion women elegant premium",
        ]
        home_keywords = [
            "premium home decor luxury modern",
            "smart home gadgets automation premium",
        ]

        # Mix the targets
        targets = [
            {"category": "Beauty & Glow", "keywords": random.choice(beauty_keywords), "count": counts["Beauty & Glow"]},
            {"category": "Elite Tech", "keywords": random.choice(tech_keywords), "count": counts["Elite Tech"]},
            {"category": "Quiet Luxury", "keywords": random.choice(luxury_keywords), "count": counts["Quiet Luxury"]},
            {"category": "Smart Home", "keywords": random.choice(home_keywords), "count": counts["Smart Home"]},
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
