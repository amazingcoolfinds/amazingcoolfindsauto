import os
import json
import logging
from groq import Groq, RateLimitError, InternalServerError, APIStatusError
from pathlib import Path
import time

class GroqQuotaExceeded(Exception):
    """Custom exception when API quota is empty"""
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("GroqGenerators")

class GroqScriptGenerator:
    def __init__(self, api_key):
        self.api_key = api_key.strip() if api_key else ""
        import httpx
        self.client = Groq(
            api_key=self.api_key,
            http_client=httpx.Client(trust_env=False, http2=True, timeout=60.0),
            max_retries=5
        )
        self.model = "llama-3.3-70b-versatile"

    def generate_script(self, product: dict) -> dict:
        """
        Generates a viral, native English video script for the product.
        Returns a dictionary with title, narration, and hashtags.
        """
        product_title = product.get('title', 'Unknown Product')
        price = product.get('price', '$20')
        category = product.get('category', 'Awesome Find')
        bullets = product.get('bullets', [])
        
        # Extract brand name if present (usually first word or before first comma)
        brand = ""
        if ',' in product_title:
            brand = product_title.split(',')[0].strip()
        else:
            brand = product_title.split()[0] if product_title else ""
        
        # Format bullets for better readability
        bullet_text = ". ".join(bullets[:4]) if bullets else "Amazing quality and features"
        
        prompt = (
            f"You are a viral TikTok/YouTube Shorts content creator. Create an engaging, native English script for this product:\n\n"
            f"PRODUCT: {product_title}\n"
            f"BRAND: {brand}\n"
            f"PRICE: {price}\n"
            f"CATEGORY: {category}\n"
            f"KEY FEATURES: {bullet_text}\n\n"
            "SCRIPT REQUIREMENTS:\n"
            "1. START with a viral hook that VARY across runs (e.g., 'POV: You just found...', 'I wasn't expecting this level of quality...', 'Does your [problem] drive you crazy?', 'The {brand} {product_title} is a total game changer')\n"

            "2. USE the product features to create a compelling, viral narrative (2-3 sentences max)\n"
            "3. HIGHLIGHT what makes it special or solves a problem\n"
            "4. END with: 'Link is in the first comment!' (MANDATORY)\n"
            "5. Keep it conversational, enthusiastic, and under 20 seconds when spoken (STRICT LIMIT: 45-55 words)\n"
            "6. Sound like a real person discovering something cool, NOT like an ad\n"
            "7. Use native English expressions and natural speech patterns\n\n"
            "Return JSON with exactly three keys:\n"
            "- 'title': A catchy, clickable video title (5-8 words)\n"
            "- 'narration': The full spoken script (natural, conversational, native English, approx 50 words)\n"
            "- 'hashtags': 4-5 viral hashtags as a list\n\n"
            "CRITICAL: Everything must be in fluent, native English. No technical jargon or ASIN codes."
        )

        for attempt in range(3):
            try:
                log.info(f"🧠 Generating Groq script for '{product_title[:50]}...' (Attempt {attempt+1})...")
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    timeout=30.0  # Add timeout
                )
                res = json.loads(chat_completion.choices[0].message.content)
                return {
                    "title": res.get("title", f"Check out this {brand}!"),
                    "narration": res.get("narration", f"I was not expecting this level of quality! The {brand} is amazing and at only {price}, it's a steal. Link is in the first comment!"),
                    "hashtags": res.get("hashtags", ["#amazonfinds", "#coolgadgets", "#musthaves", "#viral"])
                }

            except RateLimitError as e:
                log.warning(f"⏳ Groq Rate Limit hit: {e}. Waiting 10s...")
                if "quota" in str(e).lower() or "insufficient" in str(e).lower():
                    raise GroqQuotaExceeded("Groq API Quota reached its limit.")
                time.sleep(10)
            except (InternalServerError, APIStatusError) as e:
                log.warning(f"⚠️ Groq API issue: {e}. Retrying...")
                time.sleep(2)
            except Exception as e:
                error_msg = str(e).lower()
                if "connection" in error_msg or "timeout" in error_msg or "network" in error_msg:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    log.warning(f"🌐 Connection error on attempt {attempt+1}/3: {e}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    log.error(f"❌ Unexpected Groq Script error: {e}")
                    break

        # If all retries fail, return None so the pipeline can halt
        log.error("❌ Failed to generate Groq script after all retries.")
        return None

class GroqVoiceGenerator:
    def __init__(self, api_key):
        self.api_key = api_key.strip() if api_key else ""
        import httpx
        self.client = Groq(
            api_key=self.api_key,
            http_client=httpx.Client(trust_env=False, http2=True, timeout=120.0),
            max_retries=5
        )
        self.model = "canopylabs/orpheus-v1-english"
        self.voice = "diana"
        self.elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        self.elevenlabs_voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()
        if self.elevenlabs_api_key:
            log.info("✅ ElevenLabs fallback configured")
        else:
            log.warning("⚠️ ElevenLabs API key not found - no fallback available")

    def _generate_elevenlabs(self, text: str, asin: str):
        """Generate voiceover using ElevenLabs as fallback."""
        if not self.elevenlabs_api_key or not self.elevenlabs_voice_id:
            log.error("❌ ElevenLabs credentials not configured")
            return None
        
        assets_dir = Path("assets")
        assets_dir.mkdir(parents=True, exist_ok=True)
        output_path = assets_dir / f"{asin}_voice.wav"
        
        try:
            import httpx
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}",
                    headers={
                        "xi-api-key": self.elevenlabs_api_key,
                        "Content-Type": "application/json",
                        "Accept": "audio/wav"
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_turbo_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75
                        }
                    }
                )
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    log.info(f"✅ ElevenLabs Voiceover saved to {output_path}")
                    return output_path
                else:
                    log.error(f"❌ ElevenLabs API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            log.error(f"❌ ElevenLabs generation failed: {e}")
            return None

    def generate(self, text: str, asin: str):
        """
        Generates voiceover audio. Tries Groq first, falls back to ElevenLabs on quota/rate limit.
        """
        assets_dir = Path("assets")
        assets_dir.mkdir(parents=True, exist_ok=True)
        neural_path = assets_dir / f"{asin}_voice.wav"
        
        for attempt in range(3):
            try:
                log.info(f"🗣️  Generating Groq Neural Voiceover (Diana) for {asin} (Attempt {attempt+1})...")
                response = self.client.audio.speech.create(
                    model=self.model,
                    voice=self.voice,
                    response_format="wav",
                    input=text,
                    timeout=60.0
                )
                with open(neural_path, 'wb') as f:
                    if hasattr(response, 'iter_bytes'):
                        for chunk in response.iter_bytes(): f.write(chunk)
                    else:
                        f.write(response.read())
                log.info(f"✅ Groq Neural Voiceover saved to {neural_path}")
                return neural_path

            except RateLimitError as e:
                log.error(f"🛑 Groq Audio Rate Limit hit: {e}")
                if "quota" in str(e).lower() or "insufficient" in str(e).lower():
                    log.info("🔄 Attempting ElevenLabs fallback...")
                    elevenlabs_result = self._generate_elevenlabs(text, asin)
                    if elevenlabs_result:
                        return elevenlabs_result
                    raise GroqQuotaExceeded("Groq API Limit Reached - Pausing to save quota.")
                time.sleep(10)
            except Exception as e:
                error_msg = str(e).lower()
                if "connection" in error_msg or "timeout" in error_msg or "network" in error_msg:
                    wait_time = 2 ** attempt
                    log.warning(f"🌐 Voice API connection error on attempt {attempt+1}/3: {e}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    log.error(f"❌ Groq Voice API failed: {e}")
                    if "insufficient" in error_msg or "quota" in error_msg:
                        log.info("🔄 Attempting ElevenLabs fallback...")
                        elevenlabs_result = self._generate_elevenlabs(text, asin)
                        if elevenlabs_result:
                            return elevenlabs_result
                        raise GroqQuotaExceeded("Quota exhausted")
                    time.sleep(2)
        
        log.warning(f"⚠️ Groq failed, trying ElevenLabs fallback for {asin}...")
        elevenlabs_result = self._generate_elevenlabs(text, asin)
        if elevenlabs_result:
            return elevenlabs_result
        
        log.warning(f"⚠️ Failed to generate voice for {asin} after all attempts.")
        return None

class GroqProductSelector:
    def __init__(self, api_key):
        self.api_key = api_key.strip() if api_key else ""
        import httpx
        self.client = Groq(
            api_key=self.api_key,
            http_client=httpx.Client(trust_env=False, http2=True, timeout=60.0),
            max_retries=5
        )
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
            "1. Profit Potential: Prioritize high-ticket products with a price GREATER THAN $60 USD. If few products meet this criteria, you may select quality products above $30 USD. Prioritize products that maximize absolute USD commission per sale.\n"
            "2. High Commission: Target products yielding $10+ USD per sale where possible.\n"
            "3. High Rotation: BSR (Best Sellers Rank) should be < 100,000 (Prefer < 50,000).\n"
            "4. High Conversion: Rating 4.0+ (Prefer 4.3+) and Prime availability are key.\n"
            "\n"
            "5. Low Competition: Balance popularity with uniqueness.\n\n"
            f"CANDIDATES:\n{json.dumps(candidates_data, indent=2)}\n\n"
            "INSTRUCTIONS:\n"
            "- Apply a scoring system (0-100) to each product.\n"
            "- Favor products that result in HIGHER absolute USD commission.\n"
            "- Select products with Score >= 70.\n"
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
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            res = json.loads(chat_completion.choices[0].message.content)
            return res.get("category", "Life & Style")
        except:
            return "Life & Style"
