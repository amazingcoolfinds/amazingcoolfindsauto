from playwright.sync_api import sync_playwright
import time
import random

keywords = "Movers & Shakers Electronics Gadgets"
# keywords_encoded = "Movers+%26+Shakers+Electronics+Gadgets"
url = f"https://www.amazon.com/s?k={keywords.replace(' ', '+')}"

print(f"URL: {url}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    )
    page = context.new_page()
    
    try:
        print("Navigating...")
        page.goto(url, wait_until='domcontentloaded')
        time.sleep(5)
        
        print("Waiting for selector...")
        try:
            page.wait_for_selector('div[data-component-type="s-search-result"], .s-result-item', timeout=10000)
            print("Found results!")
        except Exception as e:
            print(f"Timeout: {e}")
            content = page.content()
            with open("search_failure_debug.html", "w") as f:
                f.write(content)
            print("Saved debug HTML to search_failure_debug.html")
            
            if "To discuss automated access" in content:
                print("BLOCKED: Bot detection detected")
            elif "captcha" in content.lower():
                print("BLOCKED: Captcha detected")
            else:
                print("NOT BLOCKED: Page structure changed or blank page")
                
    finally:
        browser.close()
