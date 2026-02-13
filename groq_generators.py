import os
import json
import logging
from groq import Groq
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("GroqGenerators")

class GroqScriptGenerator:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def generate_script(self, product: dict) -> dict:
        """
        Generates a viral, human-like video script for the product.
        Returns a dictionary with title, narration, and hashtags.
        """
        product_name = product.get('title', 'Unknown Product')
        price = product.get('price', '$20')
        category = product.get('category', 'Awesome Find')
        bullets = " ".join(product.get('bullets', []))
        
        # Strip technical identifiers if they snuck in
        if product_name.startswith("Product ") and len(product_name.strip()) < 20: 
            product_name = "this awesome find"
            
        prompt = (
            f"Write a short, viral TikTok script for a product named '{product_name}' in the category '{category}', priced at {price}. "
            f"Product Details: {bullets}. "
            "CRITICAL: The script MUST be about this specific product and its features. "
            "Do NOT read the ASIN or technical codes in the narration. "
            "Return the response in JSON format with exactly three keys: "
            "'title' (a catchy hook), 'narration' (the full spoken text, ~20-30s), "
            "and 'hashtags' (3-5 viral hashtags). "
            "CRITICAL: The entire response MUST be in English. "
            "The narration MUST end with the call to action: 'Check it out in first comment'. "
            "Sound enthusiastic, human, and like you're recommending it to a best friend. "
            "DO NOT include scene descriptions like '[Visual: ...]', ONLY the narration text."
        )

        try:
            log.info(f"🧠 Generating Groq script for '{product_name}'...")
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            res = json.loads(chat_completion.choices[0].message.content)
            return {
                "title": res.get("title", f"Check out this {product_name}!"),
                "narration": res.get("narration", f"You have to see this! The {product_name} is a game changer at only {price}."),
                "hashtags": res.get("hashtags", ["#amazonfinds", "#coolgadgets", "#musthaves"])
            }

        except Exception as e:
            log.error(f"Groq Script Generation failed: {e}")
            return {
                "title": f"Must Have: {product_name}",
                "narration": f"This {product_name} is absolutely amazing for only {price}. You need to check it out right now!",
                "hashtags": ["#amazonfinds", "#shopping"]
            }

class GroqVoiceGenerator:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = "canopylabs/orpheus-v1-english"
        self.voice = "diana" # Changed to Diana voice

    def generate(self, text: str, asin: str):
        """
        Generates voiceover audio using Groq (Diana) only.
        Fails fast if Groq API is not available.
        """
        # Only use Groq Neural Voice (Diana)
        neural_path = f"temp/voice_{asin}.wav"
        try:
            log.info(f"🗣️  Generating Groq Neural Voiceover (Diana) for {asin}...")
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice, # "diana"
                response_format="wav",
                input=text,
            )
            with open(neural_path, 'wb') as f:
                if hasattr(response, 'iter_bytes'):
                    for chunk in response.iter_bytes(): f.write(chunk)
                else:
                    f.write(response.read())
            log.info(f"✅ Groq Neural Voiceover saved to {neural_path}")
            return neural_path

        except Exception as e:
            log.error(f"❌ Groq Voice API failed: {e}")
            log.warning(f"⚠️ Skipping voice generation for {asin}. Product will be skipped.")
            return None

class GroqProductSelector:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def analyze_candidates(self, category: str, products: list) -> list:
        """
        Analyzes a list of product candidates and returns the top 3-5 with a score >= 70.
        Expects products to have: title, price, rating, reviews_count, is_prime, bsr, commission_rate.
        """
        if not products:
            return []

        # Simplified data for the prompt to save tokens
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
            f"You are a High-Performance Affiliate Marketing Expert. Your goal is to select the TOP 3-5 products from this list for the '{category}' category. "
            "CRITERIA FOR IDEAL PRODUCT:\n"
            "1. Profit Maximization (MANDATORY): Prioritize products with higher price points ($100+ USD) to maximize absolute commission per sale. A product costing $200 with 4% commission ($8 profit) is BETTER than a $50 product with 10% commission ($5 profit).\n"
            "2. High Commission: Target products yielding $10+ USD per sale (calculate based on price and commission_rate).\n"
            "3. High Rotation: BSR (Best Sellers Rank) should be < 50,000 in main categories.\n"
            "4. High Conversion: Rating 4.3+ and Prime availability are MUSTS.\n"
            "5. Low Competition: Balance popularity with uniqueness.\n\n"
            f"CANDIDATES:\n{json.dumps(candidates_data, indent=2)}\n\n"
            "INSTRUCTIONS:\n"
            "- Apply a scoring system (0-100) to each product.\n"
            "- Favor products that result in HIGHER absolute USD commission.\n"
            "- Select ONLY products with Score >= 70.\n"
            "- Everything in the 'reasoning' field MUST be in English.\n"
            "- Return a JSON object with a key 'selections' containing a list of objects. Each object must have 'asin', 'score', and 'reasoning'.\n"
            "- Limit to top 5 selections max."
        )

        try:
            log.info(f"🧐 AI selecting top products for {category} from {len(products)} candidates...")
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.3, # Low temperature for more deterministic selection
            )
            res = json.loads(chat_completion.choices[0].message.content)
            selections = res.get("selections", [])
            
            # Filter and map back to full product objects
            final_products = []
            for selection in selections:
                asin = selection.get("asin")
                score = selection.get("score", 0)
                if score >= 70:
                    orig_p = next((p for p in products if p['asin'] == asin), None)
                    if orig_p:
                        # Success! Add metadata
                        orig_p['selection_score'] = score
                        orig_p['selection_reasoning'] = selection.get("reasoning")
                        final_products.append(orig_p)
            
            log.info(f"✅ AI Selected {len(final_products)} high-performance products.")
            return final_products[:5]

        except Exception as e:
            log.error(f"Groq Selection failed: {e}")
            # Fallback: simple heuristic selection if AI fails
            return products[:3]
