#!/usr/bin/env python3
"""
Strategy Monitor - Strategic product discovery and profit optimization
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime

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

        # Define targets with High-Ticket leaning keywords
        targets = [
            {"category": "Lifestyle", "keywords": "premium luxury skincare sets beauty tech", "count": counts["Lifestyle"]},
            {"category": "Tech", "keywords": "high-end innovative gadgets professional electronics", "count": counts["Tech"]},
            {"category": "Home", "keywords": "luxury smart home automation designer decor", "count": counts["Home"]},
            {"category": "Auto", "keywords": "premium car electronics luxury auto accessories", "count": counts["Auto"]}
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
    print("Strategic Targets:", monitor.get_discovery_targets())
    print("Profit Test (Lifestyle, $50):", monitor.calculate_potential_profit("$50", "Lifestyle"))
