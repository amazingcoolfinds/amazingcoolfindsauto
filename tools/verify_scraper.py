from advanced_scraper import AdvancedScraper
import sys

scraper = AdvancedScraper()
print("Testing Search...")
results = scraper.search("gaming mouse", max_results=1)

if not results:
    print("Search failed to return results")
    sys.exit(1)

print(f"Found product: {results[0]['asin']}")
print("Testing Details...")
details = scraper.get_details(results[0]['asin'])

if not details:
    print("Details scraping failed (likely blocked)")
    sys.exit(1)

print("Successfully scraped details!")
print(f"Title: {details['title']}")
sys.exit(0)
