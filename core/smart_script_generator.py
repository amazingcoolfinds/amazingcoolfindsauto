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
        
        title = f"Stop Scuffing Your {vehicle.title()}! These {material.title()} Covers Are A Must"
        
        narration = f"""POV: You just found the ultimate {vehicle} upgrade with these premium {material} seat covers! 
        
They're 100% waterproof and super durable - perfect for any adventure. 
Installation is a breeze, takes just 15 minutes with no tools needed.
{' '.join([f'Features include {feature}.' for feature in features[:3]])}
        
At only {price}, these are a total game changer for your interior.
Link is in the first comment!"""

        
        hashtags = ['#CarAccessories', '#SeatCovers', f'#{vehicle.title().replace(" ", "")}', '#CarUpgrade']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_tech_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for tech gadgets"""
        title = f"This Tech Discovery Is Literally A Life Saver!"
        narration = f"""I wasn't expecting this level of quality! This tech gadget is a total game changer.
It's packed with insane features and works perfectly with all your devices.
At only {analysis['price']}, this is the one piece of tech you need this year.
Link is in the first comment!"""

        hashtags = ['#TechGadgets', '#MustHave', '#AmazonFinds']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_home_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for home decor"""
        title = f"Your Home Setup Is Missing This One Item"
        narration = f"""Most people don't know how much of a difference this one piece makes!
It's the perfect addition to any room and the quality is absolutely top-tier.
At only {analysis['price']}, it looks way more expensive than it is.
Link is in the first comment!"""

        hashtags = ['#HomeDecor', '#InteriorDesign', '#AmazonFinds']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_kitchen_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for kitchen items"""
        title = f"The Kitchen Hack You Didn't Know You Needed"
        narration = f"""Does your cooking prep drive you crazy? You need this tool!
It makes everything so much faster and the design is obsessively thought out.
Professional quality that fits right in your kitchen.
At only {analysis['price']}, it's an absolute no-brainer.
Link is in the first comment!"""

        hashtags = ['#KitchenGadgets', '#Cooking', '#AmazonFinds']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_beauty_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for beauty products"""
        title = f"The Secret To A Perfect Skincare Routine"
        narration = f"""If you're looking for the perfect addition to your routine, stop scrolling!
This product is absolutely incredible and the results speak for themselves.
Perfect for all skin types and feels so premium.
At only {analysis['price']}, your skin will thank you later.
Link is in the first comment!"""

        hashtags = ['#Beauty', '#Skincare', '#AmazonFinds']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_fitness_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for fitness items"""
        title = f"Stop Settling For Basic Workouts"
        narration = f"""POV: You just found the missing piece for your home gym setup!
This equipment is exactly what you need to hit those fitness goals.
Durable, professional grade, and built to last.
At only {analysis['price']}, it's the best investment you'll make this month.
Link is in the first comment!"""

        hashtags = ['#Fitness', '#Workout', '#HomeGym']
        
        return {
            'title': title,
            'narration': narration,
            'hashtags': hashtags
        }
    
    def _generate_general_script(self, analysis: Dict, product: Dict) -> Dict:
        """Generate script for general products"""
        title = f"The Viral Amazon Find You've Been Seeing Everywhere"
        narration = f"""I finally found it - the product everyone is talking about!
It's even better in person and the quality is absolutely insane.
If you've been on the fence, this is your sign to grab one.
At only {analysis['price']}, it's a total steal.
Link is in the first comment!"""

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