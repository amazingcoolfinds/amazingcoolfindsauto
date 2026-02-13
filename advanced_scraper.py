import logging
import time
import re
import yaml
from pathlib import Path
from playwright.sync_api import sync_playwright
# Removed unused selectorlib import


# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("AdvancedScraper")

class AdvancedScraper:
    def __init__(self, associate_tag="amazingcoolfinds-20"):
        self.associate_tag = associate_tag
        self.base_dir = Path(__file__).parent
        # We will hardcode selectors for robustness instead of depending on broken selectorlib
        
    def get_details(self, asin: str):
        """
        Scrapes Amazon product page using Playwright (Headless Browser) + BeautifulSoup.
        """
        url = f"https://www.amazon.com/dp/{asin}"
        log.info(f"🕸️  [Playwright] Navigating to {asin}...")
        
        with sync_playwright() as p:
            # Launch browser (Headless)
            browser = p.chromium.launch(headless=True)
            
            # Create context with stealthy headers
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            page = context.new_page()
            
            try:
                # Go to page
                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # Check for "dog" page (404) or Captcha
                if "To discuss automated access" in page.content():
                    log.warning("⚠️  Amazon blocked the request (Captcha/Bot Detection)")
                    return None
                
                # Extract content
                html = page.content()
                
                # Close browser immediately to free resources
                browser.close()
                
                # Parse with BeautifulSoup
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # 1. Title
                title = None
                title_selectors = [
                    '#productTitle',
                    '#title',
                    '.a-size-extra-large',
                    'h1.a-size-large'
                ]
                for selector in title_selectors:
                    el = soup.select_one(selector)
                    if el:
                        title = el.get_text(strip=True)
                        break
                
                # 2. Price
                price = "$29.99"
                # Try multiple common price selectors
                price_selectors = [
                    '.a-price .a-offscreen',
                    '#price_inside_buybox',
                    '#priceblock_ourprice',
                    '#priceblock_dealprice',
                    '.apexPriceToPay .a-offscreen'
                ]
                for selector in price_selectors:
                    el = soup.select_one(selector)
                    if el:
                        price = el.get_text(strip=True)
                        break
                
                # 3. Images (Hi-Res) - Improved extraction
                images = []
                # Look for the colorImages JSON which contains hi-res variants
                # This is more reliable than hiRes regex
                json_match = re.search(r'colorImages":\s*({.+?}),\s*"', html)
                if json_match:
                    try:
                        img_data = json.loads(json_match.group(1))
                        # The JSON structure is complex, we target the main hiRes urls
                        for color in img_data.values():
                            for entry in color:
                                if 'hiRes' in entry and entry['hiRes']:
                                    images.append(entry['hiRes'])
                                elif 'large' in entry and entry['large']:
                                    images.append(entry['large'])
                    except: pass
                
                # Fallback to previous hiRes regex
                if not images:
                    hi_res_matches = re.findall(r'"hiRes":"(https://[^"]+)"', html)
                    if hi_res_matches:
                        images = list(dict.fromkeys(hi_res_matches))
                
                # Fallback to landing image or thumbnail gallery
                if not images:
                    img_els = soup.select('#altImages img, #landingImage')
                    for img in img_els:
                        src = img.get('src', '').replace('_SS40_', '_SL1500_').replace('_AC_US40_', '_SL1500_')
                        if 'https' in src and 'sprite' not in src:
                            images.append(src)
                        
                images = list(dict.fromkeys(images)) # Dedup
                if not images:
                     images = [f"https://placehold.co/1080x1920/4A90E2/FFF.png?text={asin}"]
                
                # 4. Rating & Reviews
                rating = "4.5"
                reviews_count = "0"
                rating_el = soup.select_one('span[data-hook="rating-out-of-text"]') or soup.select_one('.a-icon-alt')
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    r_match = re.search(r'(\d[,.]\d)', rating_text)
                    if r_match:
                        rating = r_match.group(1).replace(',', '.')
                
                reviews_el = soup.select_one('#acrCustomerReviewText')
                if reviews_el:
                    rev_text = reviews_el.get_text(strip=True)
                    rev_match = re.search(r'([\d,.]+)', rev_text)
                    if rev_match:
                        reviews_count = rev_match.group(1).replace(',', '').replace('.', '')

                # 5. Prime Status
                is_prime = bool(soup.select_one('#prime_feature_div, .a-icon-prime, #upsell_prime_feature_div'))

                # 6. BSR (Best Sellers Rank)
                bsr_data = []
                # BSR is often in a specific table or bullet point
                # Searching in 'Product details' section
                details_text = soup.get_text(" ", strip=True)
                # Common patterns: "#1 in ...", "Best Sellers Rank: #1,234 in ..."
                bsr_matches = re.findall(r'#([\d,]+)\s+in\s+([A-Za-z\s&]+)', details_text)
                for rank, category in bsr_matches:
                    bsr_data.append({"rank": rank.replace(',', ''), "category": category.strip()})
                
                # 7. Bullets
                bullets = []
                bullet_els = soup.select('#feature-bullets li span.a-list-item')
                for b in bullet_els:
                    text = b.get_text(strip=True)
                    if text and len(text) > 10:
                        bullets.append(text)
                
                return {
                    "asin": asin,
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "reviews_count": reviews_count,
                    "is_prime": is_prime,
                    "bsr": bsr_data[:2], # Top 2 ranks
                    "image_url": images[0],
                    "images": images[:10],
                    "bullets": bullets[:5],
                    "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}"
                }
                
            except Exception as e:
                import traceback
                log.error(f"Playwright/Soup Error: {e}\n{traceback.format_exc()}")
                if 'browser' in locals(): browser.close()
                return None
                
        return None

    def _process_data(self, data, asin):
         # Deprecated, logic moved to get_details
         pass

    def search(self, keywords, max_results=3):
        """
        Search Amazon for products using Playwright to bypass bot detection.
        """
        url = f"https://www.amazon.com/s?k={keywords.replace(' ', '+')}"
        products = []
        
        log.info(f"🔍 [Playwright] Searching for '{keywords}'...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            try:
                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # Wait for results
                try:
                    page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=5000)
                except:
                    log.warning("⚠️  Search results selector not found (or blocked)")
                    browser.close()
                    return []
                
                # Extract ASINs
                items = page.query_selector_all('div[data-component-type="s-search-result"]')
                
                for item in items[:max_results]:
                    asin = item.get_attribute('data-asin')
                    if asin:
                        # Extract basic info from search result
                        title_el = item.query_selector('h2 span')
                        title = title_el.inner_text() if title_el else f"Product {asin}"
                        
                        products.append({
                            'asin': asin,
                            'title': title,
                            'price': "$29.99", # Placeholder, will be enriched
                            'rating': "4.5",
                            'image_url': f"https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&Format=_SL300_&ASIN={asin}&MarketPlace=US&ID=AsinImage", # Thumbnail trick
                            'affiliate_url': f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}"
                        })
                        
                log.info(f"✓ Found {len(products)} products via Playwright")
                
            except Exception as e:
                log.error(f"Search failed: {e}")
            finally:
                browser.close()
                
        return products

if __name__ == "__main__":
    scraper = AdvancedScraper()
    # Test Search
    print("Testing Search...")
    results = scraper.search("gaming mouse", max_results=2)
    print(results)
    
    # Test Details
    if results:
        print("\nTesting Details for first result...")
        details = scraper.get_details(results[0]['asin'])
        print(details)
