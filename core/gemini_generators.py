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
            f"You are a top-tier viral content creator for TikTok and YouTube Shorts. Your goal is to create a high-energy, native English script that stops the scroll.\n\n"
            f"PRODUCT: {product_title}\n"
            f"BRAND: {brand}\n"
            f"PRICE: {price}\n"
            f"CATEGORY: {category}\n"
            f"KEY FEATURES: {bullet_text}\n\n"
            "CREATIVE GUIDELINES:\n"
            "1. THE HOOK: Do NOT start every video the same way. Avoid 'Check out this' or 'You need this'. Use a unique hook: a question, a bold statement, or a relatable pain point (e.g., 'Stop scrolling if you drive a sedan' or 'This is the gadget I wish I had last year').\n"
            "2. THE BODY: Focus on the MOST impressive feature. Use vivid, sensory language. Sound like an enthusiast, not a salesman.\n"
            "3. THE CTA: End with: 'Link is in the first comment!' (MANDATORY).\n"
            "4. TIMING: Maximum 50 words. Must be spoken in under 20 seconds.\n"
            "5. TONE: High energy, native English, conversational, viral potential.\n\n"
            "Return JSON with exactly three keys:\n"
            "- 'title': A clickable, clickbait-style title (no hashtags here).\n"
            "- 'narration': The spoken script.\n"
            "- 'hashtags': 4-5 trending, relevant hashtags.\n"
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
