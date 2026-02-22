import os
import json
import logging
import time
from pathlib import Path
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("GeminiGenerators")

class GeminiScriptGenerator:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def generate_script(self, product: dict) -> dict:
        product_title = product.get('title', 'Unknown Product')
        price = product.get('price', '$20')
        category = product.get('category', 'Awesome Find')
        bullets = product.get('bullets', [])
        
        brand = ""
        if ',' in product_title:
            brand = product_title.split(',')[0].strip()
        else:
            brand = product_title.split()[0] if product_title else ""
        
        bullet_text = ". ".join(bullets[:4]) if bullets else "Amazing quality and features"
        
        prompt = (
            f"You are a viral TikTok/YouTube Shorts content creator. Create an engaging, native English script for this product:\n\n"
            f"PRODUCT: {product_title}\n"
            f"BRAND: {brand}\n"
            f"PRICE: {price}\n"
            f"CATEGORY: {category}\n"
            f"KEY FEATURES: {bullet_text}\n\n"
            "SCRIPT REQUIREMENTS:\n"
            "1. START by mentioning the brand/product name naturally\n"
            "2. USE the product features to create a compelling, viral narrative (2-3 sentences max)\n"
            "3. HIGHLIGHT what makes it special or solves a problem\n"
            "4. END with: 'Link is in the first comment!' (MANDATORY)\n"
            "5. Keep it conversational, enthusiastic, and under 20 seconds when spoken (STRICT LIMIT: 45-55 words)\n"
            "6. Sound like a real person discovering something cool, NOT like an ad\n"
            "7. Use native English expressions and natural speech patterns\n\n"
            "Return JSON with exactly three keys:\n"
            "- 'title': A catchy, clickable video title (5-8 words)\n"
            "- 'narration': The full spoken script (natural, conversational, native English, approx 50 words)\n"
            "- 'hashtags': 4-5 viral hashtags as a list\n"
        )

        for attempt in range(3):
            try:
                log.info(f"💎 Generating Gemini script for '{product_title[:50]}...' (Attempt {attempt+1})...")
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )
                res = json.loads(response.text)
                return {
                    "title": res.get("title", f"Check out this {brand}!"),
                    "narration": res.get("narration", f"You have to see this! The {brand} is a game changer at only {price}. Link is in the first comment!"),
                    "hashtags": res.get("hashtags", ["#amazonfinds", "#coolgadgets", "#musthaves", "#viral"])
                }
            except Exception as e:
                log.warning(f"⚠️ Gemini API issue: {e}. Retrying...")
                time.sleep(2)

        return None

class GeminiProductSelector:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze_candidates(self, category: str, products: list) -> list:
        if not products:
            return []

        candidates_data = []
        for p in products:
            candidates_data.append({
                "asin": p.get("asin"),
                "title": p.get("title")[:60],
                "price": p.get("price"),
                "rating": p.get("rating"),
                "reviews": p.get("reviews_count"),
                "prime": p.get("is_prime"),
                "bsr": p.get("bsr"),
                "commission_rate": p.get("commission", "4%")
            })

        prompt = (
            f"You are a High-Performance Affiliate Marketing Expert. Select the TOP 3-5 products from this list for the '{category}' category.\n"
            "CRITERIA:\n"
            "1. Profit Maximization (MANDATORY): ONLY select products with a price GREATER THAN $60 USD. If a product is below $60, its score must be 0. Prioritize products $100+ USD to maximize absolute commission per sale.\n"
            "2. High Commission: Target products yielding $10+ USD per sale.\n"
            "3. High Rotation: BSR < 50,000.\n"
            "4. High Conversion: Rating 4.3+ and Prime availability.\n\n"
            f"CANDIDATES:\n{json.dumps(candidates_data, indent=2)}\n\n"
            "Return JSON object with key 'selections' containing a list of objects with 'asin', 'score' (0-100), and 'reasoning' (in English).\n"
            "Select ONLY products with Score >= 70."
        )

        try:
            log.info(f"🧐 Gemini selecting top products for {category} from {len(products)} candidates...")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            res = json.loads(response.text)
            selections = res.get("selections", [])
            
            final_products = []
            for selection in selections:
                asin = selection.get("asin")
                score = selection.get("score", 0)
                if score >= 70:
                    orig_p = next((p for p in products if p['asin'] == asin), None)
                    if orig_p:
                        orig_p['selection_score'] = score
                        orig_p['selection_reasoning'] = selection.get("reasoning")
                        final_products.append(orig_p)
            
            log.info(f"✅ Gemini Selected {len(final_products)} high-performance products.")
            return final_products[:5]

        except Exception as e:
            log.error(f"Gemini Selection failed: {e}")
            return products[:3]
