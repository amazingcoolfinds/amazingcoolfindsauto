import logging
import time
import re
import random
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("AdvancedScraper")

class AdvancedScraper:
    def __init__(self, associate_tag="amazingcoolfinds-20"):
        self.associate_tag = associate_tag
        self.base_dir = Path(__file__).parent
        # We will hardcode selectors for robustness instead of depending on broken selectorlib
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]
        
    def get_details(self, asin: str):
        """
        Scrapes Amazon product page using Playwright (Headless Browser) + BeautifulSoup.
        """
        asin = asin.strip().upper()
        url = f"https://www.amazon.com/dp/{asin}"
        log.info(f"🕸️  [Playwright] Navigating to {asin}...")
        
        with sync_playwright() as p:
            # Launch browser (Headless)
            browser = p.chromium.launch(headless=True)
            
            # Random delay before starting
            time.sleep(random.uniform(2, 5))
            
            # Select random UA and Viewport
            ua = random.choice(self.user_agents)
            
            # Create context with stealthy headers
            context = browser.new_context(
                user_agent=ua,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Referer': 'https://www.amazon.com/',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            )
            
            page = context.new_page()
            
            try:
                # Go to page with longer timeout and wait_until='load'
                page.goto(url, timeout=60000, wait_until='load')
                
                # Check for "dog" page (404) or Captcha
                content = page.content()
                if "To discuss automated access" in content or "robot check" in content.lower():
                    log.warning("⚠️  Amazon blocked the request (Captcha/Bot Detection)")
                    browser.close()
                    return None
                
                # Extract content
                html = content
                
                # Close browser explicitly
                browser.close()
                
                # Parse with BeautifulSoup
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # 1. Title
                title = None
                title_selectors = ['#productTitle', '#title', '.a-size-extra-large']
                for selector in title_selectors:
                    el = soup.select_one(selector)
                    if el:
                        title = el.get_text(strip=True)
                        break
                
                if not title: 
                    return None

                # 2. Price
                price = "$29.99"
                price_selectors = ['.a-price .a-offscreen', '#price_inside_buybox', '#priceblock_ourprice']
                for selector in price_selectors:
                    el = soup.select_one(selector)
                    if el:
                        price = el.get_text(strip=True)
                        break
                
                # 3. Images (Hi-Res) - Enhanced multi-stage extraction
                images = []
                
                # A. Main Image Dynamic Data (Highest priority for main image)
                landing_img = soup.select_one('#landingImage, #imgBlkFront, #ebooksImgBlkFront')
                if landing_img and landing_img.get('data-a-dynamic-image'):
                    try:
                        dyn_data = json.loads(landing_img.get('data-a-dynamic-image'))
                        sorted_urls = sorted(dyn_data.items(), key=lambda x: x[1][0] * x[1][1], reverse=True)
                        if sorted_urls:
                            images.append(sorted_urls[0][0])
                    except: 
                        pass

                # B. Gallery JSON (colorImages)
                json_match = re.search(r'colorImages":\s*({.+?}),\s*"', html)
                if not json_match:
                    json_match = re.search(r'\'colorImages\':\s*({.+?}),', html)
                
                if json_match:
                    try:
                        img_data = json.loads(json_match.group(1))
                        for color in img_data.values():
                            for entry in color:
                                # Prioritize hiRes, then large
                                img_url = entry.get('hiRes') or entry.get('large') or entry.get('main', {}).get('url')
                                if img_url and 'https' in img_url and 'sprite' not in img_url:
                                    images.append(img_url)
                    except: 
                        pass
                
                # C. Manual Scrape + Universal High-Res Transformer
                if len(images) < 5:
                    img_els = soup.select('#altImages img, #landingImage, .a-dynamic-image')
                    for img in img_els:
                        src = img.get('src') or img.get('data-old-hires') or img.get('data-a-dynamic-image')
                        if src and 'https' in src and 'sprite' not in src:
                            hi_res_src = re.sub(r'\._[A-Z0-9,._]+_\.(jpg|jpeg|png|gif)', r'._SL1500_.\1', src)
                            images.append(hi_res_src)
                        
                # Dedup while preserving order
                seen = set()
                final_images = []
                for img in images:
                    if img not in seen and len(img) > 20:
                        img_lower = img.lower()
                        # Skip known bad patterns
                        if any(bad in img_lower for bad in ['prime', 'primes', 'sprite', 'sprite2', 'mp4', 'vid']):
                            continue
                        # Skip small thumbnail patterns (SS40, SS50, US40, US50, SR38,50, etc)
                        if re.search(r'\._(SS|AC_US|US|SR)\d+[,\d]*_\.', img):
                            continue
                        # Skip very short URLs (likely invalid)
                        if len(img) < 50:
                            continue
                        final_images.append(img)
                        seen.add(img)
                
                # Sort by resolution preference: SL1500 > SX1500 > SX679 > SX522 > SX466 > others
                def img_quality_key(url):
                    if '_SL1500_' in url or '_SX1500_' in url: return 100
                    if '_SX1000_' in url: return 95
                    if '_SX800_' in url: return 90
                    if '_SX679_' in url: return 85
                    if '_SX522_' in url: return 80
                    if '_SX466_' in url: return 75
                    if '_SX' in url: return 70
                    return 50  # Unknown format, lower priority
                
                final_images.sort(key=img_quality_key, reverse=True)
                
                # 4. Canonical Affiliate URL Builder (Fixes the tracking and format issues)
                affiliate_url = f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}"
                
                # Return the complete cleaned data structure
                return {
                    "asin": asin,
                    "title": title,
                    "price": price,
                    "images": final_images[:6],  # Max 6 high-res images for the video pipeline
                    "url": affiliate_url
                }

            except Exception as e:
                log.error(f"❌ Error scraping {asin}: {str(e)}")
                try:
                    browser.close()
                except:
                    pass
                return None

    def search(self, keywords: str, max_results: int = 3):
        """Return basic Amazon search-result data for the discovery pipeline.

        ``enhanced_pipeline.py`` deliberately obtains full product details only
        after selecting candidates.  This method supplies the light-weight
        search data used for that selection.
        """
        from urllib.parse import quote_plus

        url = f"https://www.amazon.com/s?k={quote_plus(keywords)}"
        products = []
        log.info("🔍 [Playwright] Searching for '%s'...", keywords)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="America/New_York",
                    extra_http_headers={
                        "Referer": "https://www.amazon.com/",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                page = context.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                time.sleep(random.uniform(2, 5))
                page.wait_for_selector(
                    'div[data-component-type="s-search-result"], .s-result-item',
                    timeout=20000,
                )

                items = page.query_selector_all('div[data-component-type="s-search-result"]')
                if not items:
                    items = page.query_selector_all('.s-result-item[data-asin]')

                for item in items[:max_results]:
                    asin = item.get_attribute("data-asin")
                    if not asin:
                        continue
                    try:
                        title_el = item.query_selector("h2 span")
                        price_el = item.query_selector(".a-price .a-offscreen")
                        rating_el = item.query_selector("i.a-icon-star-small span, i.a-icon-star span")
                        reviews_el = item.query_selector('span[aria-label*="reviews"], .a-size-small .a-link-normal')

                        rating_text = rating_el.inner_text() if rating_el else "0.0"
                        rating_match = re.search(r"(\d[,.]\d)", rating_text)
                        reviews_text = (
                            (reviews_el.get_attribute("aria-label") or reviews_el.inner_text())
                            if reviews_el else "0"
                        )
                        reviews_match = re.search(r"([\d,.]+)", reviews_text)

                        products.append({
                            "asin": asin,
                            "title": title_el.inner_text() if title_el else f"Product {asin}",
                            "price": price_el.inner_text() if price_el else "$0.00",
                            "rating": rating_match.group(1).replace(",", ".") if rating_match else "0.0",
                            "reviews_count": reviews_match.group(1).replace(",", "").replace(".", "") if reviews_match else "0",
                            "is_prime": bool(item.query_selector(".a-icon-prime")),
                            "image_url": f"https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&Format=_SL600_&ASIN={asin}&MarketPlace=US&ID=AsinImage",
                            "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}",
                        })
                    except Exception as exc:
                        log.warning("Failed to parse search result %s: %s", asin, exc)
            except Exception as exc:
                log.error("Search failed for '%s': %s", keywords, exc)
                return []
            finally:
                browser.close()

        log.info("✓ Found %d products with basic info via Playwright", len(products))
        return products
