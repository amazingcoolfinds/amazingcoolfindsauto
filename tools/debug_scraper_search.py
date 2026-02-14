import logging
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("DebugScraper")

def debug_search(keywords):
    url = f"https://www.amazon.com/s?k={keywords.replace(' ', '+')}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a more realistic user agent
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        try:
            log.info(f"Navigating to {url}")
            page.goto(url, wait_until='domcontentloaded')
            time.sleep(5) # Wait for potential redirects/captchas
            
            # Save screenshot
            screenshot_path = "amazon_search_debug.png"
            page.screenshot(path=screenshot_path)
            log.info(f"Screenshot saved to {screenshot_path}")
            
            # Save HTML
            html_path = "amazon_search_debug.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            log.info(f"HTML saved to {html_path}")
            
            # Check for results
            results = page.query_selector_all('div[data-component-type="s-search-result"]')
            log.info(f"Found {len(results)} search results.")
            
            if len(results) == 0:
                if "To discuss automated access" in page.content() or "captcha" in page.content().lower():
                    log.error("Detectado bloqueo de bot / Captcha")
                else:
                    log.warning("No se encontraron resultados ni bloqueo evidente. Posible cambio de selectores.")
            
        except Exception as e:
            log.error(f"Error during debug: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_search("Movers & Shakers Electronics Gadgets")
