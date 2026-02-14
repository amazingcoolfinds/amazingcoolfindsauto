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
        url = f"https://www.amazon.com/dp/{asin}"
        log.info(f"🕸️  [Playwright] Navigating to {asin}...")
        
        with sync_playwright() as p:
            # Launch browser (Headless)
            browser = p.chromium.launch(headless=True)
            
            import random
            
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
                # Go to page
                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # Check for "dog" page (404) or Captcha
                content = page.content()
                if "To discuss automated access" in content or "robot check" in content.lower():
                    log.warning("⚠️  Amazon blocked the request (Captcha/Bot Detection)")
                    return None
                
                # Extract content
                html = content
                
                # Close browser explicitly
                browser.close()
                
                # Parse with BeautifulSoup
                from bs4 import BeautifulSoup
                import json
                soup = BeautifulSoup(html, 'html.parser')
                
                # 1. Title
                title = None
                title_selectors = ['#productTitle', '#title', '.a-size-extra-large']
                for selector in title_selectors:
                    el = soup.select_one(selector)
                    if el:
                        title = el.get_text(strip=True)
                        break
                
                if not title: return None

                # 2. Price
                price = "$29.99"
                price_selectors = ['.a-price .a-offscreen', '#price_inside_buybox', '#priceblock_ourprice']
                for selector in price_selectors:
                    el = soup.select_one(selector)
                    if el:
                        price = el.get_text(strip=True)
                        break
                
                # 3. Images (Hi-Res) - Improved extraction
                images = []
                json_match = re.search(r'colorImages":\s*({.+?}),\s*"', html)
                if json_match:
                    try:
                        img_data = json.loads(json_match.group(1))
                        for color in img_data.values():
                            for entry in color:
                                url = entry.get('hiRes') or entry.get('large')
                                if url and 'https' in url and 'sprite' not in url:
                                    images.append(url)
                    except: pass
                
                if not images:
                    img_els = soup.select('#altImages img, #landingImage')
                    for img in img_els:
                        src = img.get('src', '').replace('_SS40_', '_SL1500_').replace('_AC_US40_', '_SL1500_')
                        if 'https' in src and 'sprite' not in src:
                            images.append(src)
                        
                images = [img for img in list(dict.fromkeys(images)) if len(img) > 20] # Dedup & filter short URLs
                
                if not images:
                    log.warning(f"⚠️ No valid images found for {asin}. Skipping.")
                    return None
                
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
        from urllib.parse import quote_plus
        url = f"https://www.amazon.com/s?k={quote_plus(keywords)}"
        products = []
        
        log.info(f"🔍 [Playwright] Searching for '{keywords}'...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            import random
            
            # Select random UA
            ua = random.choice(self.user_agents)
            
            # Create context with stealthy headers (Unified with get_details)
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
                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # Increase timeout and add random wait to mimic human behavior
                time.sleep(random.uniform(2, 5))
                
                try:
                    # Increased timeout to 20s for GitHub Actions / slower networks
                    page.wait_for_selector('div[data-component-type="s-search-result"], .s-result-item', timeout=20000)
                except:
                    # Check for bot detection specifically
                    content = page.content()
                    if "To discuss automated access" in content or "captcha" in content.lower():
                        log.error("❌ Amazon blocked search (Captcha/Bot Detection)")
                    else:
                        log.warning("⚠️  Search results selector not found (Timeout or Page Structure Change)")
                    
                    # Log snippet of body for debugging
                    log.debug(f"Page Content Snippet: {content[:500]}")
                    
                    # Save error page for manual inspection if needed
                    debug_file = self.base_dir / "logs" / f"search_error_{int(time.time())}.html"
                    debug_file.parent.mkdir(exist_ok=True)
                    with open(debug_file, "w") as f:
                        f.write(content)
                    log.error(f"Saved failed search HTML to {debug_file}")
                    
                    browser.close()
                    return []
                
                # Extract ASINs - using multiple possible selectors
                items = page.query_selector_all('div[data-component-type="s-search-result"]')
                if not items:
                    items = page.query_selector_all('.s-result-item[data-asin]')
                
                for item in items[:max_results]:
                    asin = item.get_attribute('data-asin')
                    if not asin: continue
                    
                    try:
                        # Extract basic info from search result
                        title_el = item.query_selector('h2 span')
                        title = title_el.inner_text() if title_el else f"Product {asin}"
                        
                        # Extract Price
                        price = "$0.00"
                        price_el = item.query_selector('.a-price .a-offscreen')
                        if price_el:
                            price = price_el.inner_text()
                        
                        # Extract Rating
                        rating = "0.0"
                        rating_el = item.query_selector('i.a-icon-star-small span, i.a-icon-star span')
                        if rating_el:
                            rating_text = rating_el.inner_text()
                            r_match = re.search(r'(\d[,.]\d)', rating_text)
                            if r_match:
                                rating = r_match.group(1).replace(',', '.')
                        
                        # Extract Reviews
                        reviews = "0"
                        reviews_el = item.query_selector('span[aria-label*="reviews"], .a-size-small .a-link-normal')
                        if reviews_el:
                            rev_text = reviews_el.get_attribute('aria-label') or reviews_el.inner_text()
                            rev_match = re.search(r'([\d,.]+)', rev_text)
                            if rev_match:
                                reviews = rev_match.group(1).replace(',', '').replace('.', '')

                        # Extract Prime
                        is_prime = bool(item.query_selector('.a-icon-prime'))

                        products.append({
                            'asin': asin,
                            'title': title,
                            'price': price,
                            'rating': rating,
                            'reviews_count': reviews,
                            'is_prime': is_prime,
                            'image_url': f"https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&Format=_SL300_&ASIN={asin}&MarketPlace=US&ID=AsinImage",
                            'affiliate_url': f"https://www.amazon.com/dp/{asin}?tag={self.associate_tag}"
                        })
                    except Exception as e:
                        log.warning(f"Failed to parse item {asin}: {e}")
                        
                log.info(f"✓ Found {len(products)} products with basic info via Playwright")
                
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
