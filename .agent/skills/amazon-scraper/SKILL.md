---
name: amazon-scraper
description: Scrapes Amazon product details (title, price, rating, images, bullets) using a local Python script. Use this skill when you need to extract structured data from an Amazon product URL or ASIN.
---

# Amazon Scraper

This skill allows you to scrape detailed product information from Amazon, including high-resolution images, using a local Python script.

## Usage

To scrape a product, use the `scripts/scrape.py` script with an ASIN or URL.

### Command

```bash
python3 .agent/skills/amazon-scraper/scripts/scrape.py <ASIN_OR_URL>
```

### Output

The script returns a JSON object with the following fields:
- `asin`: The product ASIN
- `title`: Product title
- `price`: Current price
- `rating`: Customer rating
- `image_url`: Main image URL
- `images`: List of high-res image URLs (for valid carousel generation)
- `bullets`: List of key product features

## Examples

**Scrape by ASIN:**
```bash
python3 .agent/skills/amazon-scraper/scripts/scrape.py B08N5KWB9H
```

**Scrape by URL:**
```bash
python3 .agent/skills/amazon-scraper/scripts/scrape.py "https://www.amazon.com/dp/B08N5KWB9H"
```

## Requirements

- `requests`
- `fake-useragent`
- `beautifulsoup4` (implied by content parsing)
