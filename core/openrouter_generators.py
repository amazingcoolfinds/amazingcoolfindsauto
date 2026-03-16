import os
import json
import logging
import time
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("OpenRouterGenerators")

class OpenRouterScriptGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = "openai/gpt-4o-mini"

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
            f"You are a visionary viral content creator for TikTok and YouTube Shorts. Your mission is to craft a high-energy, stop-the-scroll video script that makes people fall in love with the product's value and brand story.\n\n"
            f"PRODUCT: {product_title}\n"
            f"BRAND: {brand}\n"
            f"CATEGORY: {category}\n"
            f"KEY FEATURES: {bullet_text}\n\n"
            "CREATIVE GUIDELINES:\n"
            "1. THE HOOK (Scroll-Stopper): STRICTLY FORBIDDEN openers: 'Check this out', 'You need this', 'You need to see', 'Look at this'. ANY script starting with these phrases will be REJECTED. Use one of these formats to VARY structure across runs:\n"
            "   - Relatable Pain Point: 'Does your [Pain Point Related to Category] drive you crazy?'\n"
            "   - Bold Prediction: 'This [Product Name] is literally going to save you [Time/Space/Hassle] this year.'\n"
            "   - Curiosity Gap: 'Most people don't know [Brand] solved the biggest problem with [Category].'\n"
            "   - Visual Hook: 'I wasn't expecting this level of quality from the [Brand] [Product Name].'\n"
            "   - Gift Idea: 'If you're looking for the perfect gift for a [Category] lover, stop scrolling.'\n"
            "   - Life Hack: 'Here's a [Category] hack that actually works, thanks to [Brand].'\n"
            "   - POV: 'POV: You just found the missing piece for your [Category] setup.'\n"
            "   - Shock Value: 'Wait — this [Product] costs HOW MUCH? And it still sold out?'\n"

            "2. THE NARRATIVE (Brand & Utility Focus): Focus on the MOST impressive feature and how it actually changes the user's life. Use evocative, high-sensory language (e.g., 'silky smooth', 'obsessively designed', 'industrial-grade').\n"
            "3. PRICE POLICY: Only mention the price if it is an absolute steal (e.g., 'At just {price}, it's a no-brainer'). Otherwise, focus entirely on the VALUE and quality of {brand}.\n"
            "4. CALL TO ACTION: End with: 'Link is in the first comment!' (MANDATORY).\n"
            "5. CONSTRAINTS: Max 50 words. Natural, conversational, high-energy native English.\n\n"
            "Return JSON with exactly three keys:\n"
            "- 'title': A click-worthy, curiosity-inducing title (no hashtags).\n"
            "- 'narration': The spoken script.\n"
            "- 'hashtags': 4-5 trending, niche-relevant hashtags.\n"
        )

        for attempt in range(3):
            try:
                log.info(f"🤖 Generating OpenRouter script for '{product_title[:50]}...' (Attempt {attempt+1})...")
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/amazingcoolfindsauto",
                    "X-Title": "AmazingCoolFinds"
                }
                data = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                res = response.json()
                content = res["choices"][0]["message"]["content"]
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                try:
                    script_data = json.loads(content)
                except json.JSONDecodeError:
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        script_data = json.loads(json_match.group())
                    else:
                        raise ValueError("Could not parse JSON from response")
                return {
                    "title": script_data.get("title", f"Check out this {brand}!"),
                    "narration": script_data.get("narration", f"POV: You just found the ultimate {category} upgrade. The {brand} is a total game changer for your daily routine. Link is in the first comment!"),
                    "hashtags": script_data.get("hashtags", ["#amazonfinds", "#coolgadgets", "#musthaves", "#viral"])
                }
            except Exception as e:
                log.warning(f"⚠️ OpenRouter API issue: {e}. Retrying...")
                time.sleep(5)

        return None


class OpenRouterProductSelector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = "openai/gpt-4o-mini"

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
            "1. Profit Potential: Prioritize products with a price GREATER THAN $60 USD where possible. If a product is below $30, it should generally be avoided unless it has exceptional reviews and high volume.\n"
            "2. High Commission: Target products with high absolute commission potential (Price * Commission Rate).\n"
            "3. High Rotation: BSR < 100,000 (Prefer < 50,000).\n"
            "4. High Conversion: Rating 4.0+ (Prefer 4.3+) and Prime availability.\n\n"
            f"CANDIDATES:\n{json.dumps(candidates_data, indent=2)}\n\n"
            "Return JSON object with key 'selections' containing a list of objects with 'asin', 'score' (0-100), and 'reasoning' (in English).\n"
            "Select products with Score >= 70. If few products meet high-ticket criteria, you may select the best available candidates above $30."
        )

        try:
            log.info(f"🤖 OpenRouter selecting top products for {category} from {len(products)} candidates...")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/amazingcoolfindsauto",
                "X-Title": "AmazingCoolFinds"
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            res = response.json()
            content = res["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            try:
                selections = json.loads(content).get("selections", [])
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    selections = json.loads(json_match.group()).get("selections", [])
                else:
                    selections = []
            
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
            
            log.info(f"✅ OpenRouter Selected {len(final_products)} high-performance products.")
            return final_products[:5]

        except Exception as e:
            log.error(f"OpenRouter Selection failed: {e}")
            return products[:3]

    def classify_product(self, product: dict) -> str:
        """Classifies a product into one of the three consolidated categories."""
        product_title = product.get('title', '')
        bullets = ". ".join(product.get('bullets', []))
        
        prompt = (
            "Classify this Amazon product into EXACTLY one of these three categories:\n"
            "1. 'Tech' (Laptops, smartphones, headphones, gaming consoles, smart home hubs, cameras)\n"
            "2. 'Life & Style' (Skincare, makeup, fashion, jewelry, watches, yoga/fitness, fragrance, wellness)\n"
            "3. 'Home & Auto' (Kitchen appliances, blenders, coffee makers, home furniture, car accessories, power tools, decor)\n\n"
            "EXAMPLES:\n"
            "- 'Ninja Blender' -> 'Home & Auto'\n"
            "- 'Face Serum' -> 'Life & Style'\n"
            "- 'Wireless Mouse' -> 'Tech'\n"
            "- 'Car Dash Cam' -> 'Home & Auto'\n\n"
            f"PRODUCT TITLE: {product_title}\n"
            f"KEY FEATURES: {bullets}\n\n"
            "Return JSON with key 'category'."
        )

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/amazingcoolfindsauto",
                "X-Title": "AmazingCoolFinds"
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            res = response.json()
            content = res["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            try:
                return json.loads(content).get("category", "Life & Style")
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group()).get("category", "Life & Style")
                return "Life & Style"
        except:
            return "Life & Style"
