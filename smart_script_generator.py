#!/usr/bin/env python3
"""
Smart Script Generator - Creates context-aware scripts for any product
"""
import re
import json
import logging
from typing import Dict, List

log = logging.getLogger("SmartScriptGenerator")

class SmartScriptGenerator:
    """Creates context-aware scripts based on product analysis"""
    
    def __init__(self):
        # Product type patterns
        self.product_patterns = {
            'car_accessories': [
                'car seat covers', 'seat covers', 'car accessories', 'auto accessories',
                'floor mats', 'steering wheel cover', 'phone holder', 'car mount',
                'dash cam', 'car charger', 'trunk organizer', 'car cover'
            ],
            'tech_gadgets': [
                'phone case', 'headphones', 'bluetooth', 'wireless', 'charger',
                'cable', 'adapter', 'keyboard', 'mouse', 'monitor', 'laptop',
                'flashlight', 'lumens', 'edc', 'nitecore', 'torch', 'led'
            ],
            'home_decor': [
                'vase', 'decor', 'pillow', 'curtain', 'rug', 'wall art',
                'lamp', 'candle', 'picture frame', 'mirror', 'clock'
            ],
            'kitchen': [
                'knife', 'cutting board', 'pan', 'pot', 'blender', 'mixer',
                'coffee maker', 'toaster', 'air fryer', 'storage container'
            ],
            'beauty': [
                'skincare', 'cream', 'serum', 'moisturizer', 'face mask',
                'lipstick', 'makeup', 'brush', 'hair', 'nail'
            ],
            'fitness': [
                'yoga mat', 'dumbbell', 'resistance band', 'fitness tracker',
                'exercise bike', 'treadmill', 'protein', 'workout'
            ]
        }
        
        # Feature extraction patterns
        self.feature_patterns = {
            'material': [
                'leather', 'nappa', 'fabric', 'vinyl', 'silicone', 'plastic',
                'metal', 'wood', 'glass', 'ceramic', 'carbon fiber'
            ],
            'quality': [
                'premium', 'luxury', 'professional', 'heavy duty', 'durable',
                'waterproof', 'weatherproof', 'scratch resistant', 'fade resistant'
            ],
            'compatibility': [
                'compatible', 'fits', 'for', 'universal', 'adjustable',
                'custom fit', 'easy install', 'plug and play'
            ],
            'vehicle': [
                'dodge', 'ford', 'chevy', 'toyota', 'honda', 'bmw', 'mercedes',
                'durango', 'f-150', 'silverado', 'camry', 'civic', 'x5', 'c-class'
            ]
        }
    
    def analyze_product(self, product: Dict) -> Dict:
        """Analyze product and extract key information"""
        title = product.get('title', '').lower()
        bullets = [b.lower() for b in product.get('bullets', [])]
        all_text = f"{title} {' '.join(bullets)}"
        
        analysis = {
            'product_type': self._detect_product_type(all_text),
            'vehicle_type': self._detect_vehicle_type(all_text),
            'material': self._detect_material(all_text),
            'quality': self._detect_quality(all_text),
            'compatibility': self._detect_compatibility(all_text),
            'key_features': self._extract_key_features(all_text),
            'price': product.get('price', '$20'),
            'rating': product.get('rating', '4.5')
        }
        
        log.info(f"📊 Product Analysis: {analysis['product_type']} for {analysis.get('vehicle_type', 'general')}")
        return analysis
    
    def _detect_product_type(self, text: str) -> str:
        """Detect product type from text"""
        for product_type, patterns in self.product_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return product_type
        return 'general'
    
    def _detect_vehicle_type(self, text: str) -> str:
        """Detect vehicle type from text"""
        for pattern in self.feature_patterns['vehicle']:
            if pattern in text:
                return pattern
        return 'general'
    
    def _detect_material(self, text: str) -> str:
        """Detect material from text"""
        for pattern in self.feature_patterns['material']:
            if pattern in text:
                return pattern
        return 'standard'
    
    def _detect_quality(self, text: str) -> List[str]:
        """Detect quality indicators from text"""
        qualities = []
        for pattern in self.feature_patterns['quality']:
            if pattern in text:
                qualities.append(pattern)
        return qualities
    
    def _detect_compatibility(self, text: str) -> List[str]:
        """Detect compatibility features from text"""
        compat = []
        for pattern in self.feature_patterns['compatibility']:
            if pattern in text:
                compat.append(pattern)
        return compat
    
    def _extract_key_features(self, text: str) -> List[str]:
        """Extract key features from text"""
        features = []
        
        # Common feature patterns
        feature_patterns = [
            r'(\d+ seats?)',
            r'(\d+ year warranty?)',
            r'(easy install)',
            r'(waterproof)',
            r'(durable)',
            r'(premium)',
            r'(luxury)',
            r'(custom fit)',
            r'(airbag compatible)',
            r'(machine washable)'
        ]
        
        for pattern in feature_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            features.extend(matches)
        
        return list(set(features))  # Remove duplicates
    
    def generate_script(self, product: Dict) -> Dict:
        """Generate context-aware script for product"""
        analysis = self.analyze_product(product)
        
        # Generate script based on product type
        if analysis['product_type'] == 'car_accessories':
            return self._generate_car_script(analysis, product)
        elif analysis['product_type'] == 'tech_gadgets':
            return self._generate_tech_script(analysis, product)
        elif analysis['product_type'] == 'home_decor':
            return self._generate_home_script(analysis, product)
        elif analysis['product_type'] == 'kitchen':
            return self._generate_kitchen_script(analysis, product)
        elif analysis['product_type'] == 'beauty':
            return self._generate_beauty_script(analysis, product)
        elif analysis['product_type'] == 'fitness':
            return self._generate_fitness_script(analysis, product)
        else:
            return self._generate_general_script(analysis, product)
    
    def _generate_car_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for car accessories"""
        vehicle = analysis.get('vehicle_type', 'your vehicle')
        material = analysis.get('material', 'premium material')
        features = analysis.get('key_features', [])
        price = analysis['price']
        
        title = f"Transform Your {vehicle.title()} With These {material.title()} Seat Covers"
        
        narration = f"""Upgrade your {vehicle} with these premium {material} seat covers! 
        
They're 100% waterproof and super durable - perfect for any adventure. 
Installation takes just 15 minutes with no tools needed.
{' '.join([f'Features include {feature}.' for feature in features[:3]])}

At only {price}, these seat covers will keep your car looking brand new.
Check out the first comment for the link!"""
        
        hashtags = ['#CarAccessories', '#SeatCovers', f'#{vehicle.title().replace(" ", "")}', '#CarUpgrade']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_tech_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for tech gadgets"""
        title = f"This Tech Gadget Will Change Your Life!"
        narration = f"""You won't believe what this tech gadget can do! 
It's packed with amazing features and works perfectly with all your devices.
At only {analysis['price']}, this is a must-have for 2026.
Check out the first comment for the link!"""
        hashtags = ['#TechGadgets', '#MustHave', '#AmazonFinds']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_home_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for home decor"""
        title = f"Beautiful Home Decor You Need!"
        narration = f"""Transform your home with this beautiful decor piece!
It's the perfect addition to any room and looks absolutely stunning.
At only {analysis['price']}, this is a steal!
Check out the first comment for the link!"""
        hashtags = ['#HomeDecor', '#InteriorDesign', '#AmazonFinds']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_kitchen_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for kitchen items"""
        title = f"This Kitchen Tool Is A Game Changer!"
        narration = f"""You need this kitchen tool in your life!
It makes cooking so much easier and faster.
Perfect quality and amazing design.
At only {analysis['price']}, it's a must-have!
Check out the first comment for the link!"""
        hashtags = ['#KitchenGadgets', '#Cooking', '#AmazonFinds']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_beauty_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for beauty products"""
        title = f"This Beauty Product Is Amazing!"
        narration = f"""Your skincare routine needs this product!
It's absolutely incredible and works wonders.
Perfect for all skin types.
At only {analysis['price']}, you can't go wrong!
Check out the first comment for the link!"""
        hashtags = ['#Beauty', '#Skincare', '#AmazonFinds']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_fitness_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for fitness items"""
        title = f"Take Your Fitness To The Next Level!"
        narration = f"""This fitness equipment is exactly what you need!
Perfect for home workouts and getting in shape.
Durable, professional quality.
At only {analysis['price']}, it's a great investment!
Check out the first comment for the link!"""
        hashtags = ['#Fitness', '#Workout', '#HomeGym']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_general_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for general products"""
        title = f"This Product Is Absolutely Amazing!"
        narration = f"""You have to check out this incredible product!
It's exactly what you've been looking for.
Amazing quality and great price.
At only {analysis['price']}, it's a steal!
Check out the first comment for the link!"""
        hashtags = ['#AmazonFinds', '#MustHave', '#Shopping']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }

if __name__ == "__main__":
    # Test with the current product
    from advanced_scraper import AdvancedScraper
    
    scraper = AdvancedScraper()
    product = scraper.get_details('B0FVDC5TC7')
    
    generator = SmartScriptGenerator()
    script = generator.generate_script(product)
    
    print("🎯 SMART SCRIPT GENERATION TEST")
    print("=" * 50)
    print(f"Product: {product['title'][:50]}...")
    print(f"Generated Script:")
    print(f"Title: {script['title']}")
    print(f"Narration: {script['narration']}")
    print(f"Hashtags: {script['hashtags']}")