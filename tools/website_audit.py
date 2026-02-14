import json
from pathlib import Path

def audit_website():
    base_dir = Path("/Users/zoomies/Desktop/liveitupdeals/amazing/data")
    
    # 1. Audit Products
    products_file = base_dir / "products.json"
    if products_file.exists():
        with open(products_file, 'r') as f:
            products = json.load(f)
        
        initial_count = len(products)
        clean_products = []
        for p in products:
            img_url = p.get('image_url', '')
            images = p.get('images', [])
            
            # STRICTOR CHECK: Must have at least one Amazon-hosted image
            has_amazon_primary = "m.media-amazon.com" in img_url
            has_amazon_gallery = any("m.media-amazon.com" in img for img in images)
            
            # Reject if only AI or placeholder
            is_ai_only = "pollinations.ai" in img_url or "placehold.co" in img_url
            
            if (has_amazon_primary or has_amazon_gallery) and not is_ai_only:
                # Extra safety: if primary is bad but gallery has good ones, promote first gallery image
                if not has_amazon_primary and has_amazon_gallery:
                    p['image_url'] = next(img for img in images if "m.media-amazon.com" in img)
                clean_products.append(p)
        
        with open(products_file, 'w') as f:
            json.dump(clean_products, f, indent=2)
        
        # Also sync to main data dir
        main_data_file = Path("/Users/zoomies/Desktop/liveitupdeals/data/products.json")
        if main_data_file.exists():
             with open(main_data_file, 'w') as f:
                json.dump(clean_products, f, indent=2)

        print(f"✅ Products Audited: {initial_count} -> {len(clean_products)} (Removed {initial_count - len(clean_products)} low-quality/no-image items)")

    # 2. Audit Articles (Remove duplicates by title or slug)
    articles_file = base_dir / "articles.json"
    if articles_file.exists():
        with open(articles_file, 'r') as f:
            articles = json.load(f)
        
        initial_count = len(articles)
        unique_articles = []
        seen_slugs = set()
        
        for art in articles:
            slug = art.get('slug')
            if slug not in seen_slugs:
                unique_articles.append(art)
                seen_slugs.add(slug)
        
        with open(articles_file, 'w') as f:
            json.dump(unique_articles, f, indent=2)
        
        print(f"✅ Articles Audited: {initial_count} -> {len(unique_articles)} (Removed {initial_count - len(unique_articles)} duplicates)")

if __name__ == "__main__":
    audit_website()
