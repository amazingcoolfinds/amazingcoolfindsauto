#!/usr/bin/env python3
"""
FIXED ENHANCED WEBSITE LINK GENERATOR - Unique ID + Smooth Scroll
"""
import os
import hashlib
import time
import json
from pathlib import Path

def generate_unique_product_id(product):
    """Generate unique identifier for each product with timestamp"""
    # Create unique hash with ASIN + timestamp + random factor
    timestamp = str(int(time.time()))
    random_factor = str(hash(product['asin'] + timestamp))[:8]
    unique_string = f"{product['asin']}-{timestamp}-{random_factor}"
    
    # Create short unique ID (first 12 chars of hash)
    unique_id = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    return unique_id

def get_enhanced_website_link(product):
    """Generate enhanced website link with unique ID and scroll parameters"""
    base_url = os.getenv("WEBSITE_URL", "https://amazing-cool-finds.com")
    unique_id = generate_unique_product_id(product)
    
    # Enhanced link with scroll and product data
    enhanced_link = f"{base_url}/item/{unique_id}#product-{product['asin']}"
    
    return {
        'link': enhanced_link,
        'unique_id': unique_id,
        'scroll_target': f"product-{product['asin']}",
        'full_url': enhanced_link
    }

def create_enhanced_article_html(product):
    """Create enhanced article HTML with smooth scroll and product highlighting"""
    unique_id = generate_unique_product_id(product)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{product['title']} — Amazing Cool Finds</title>
    <link rel="icon" href="https://i.imgur.com/buAiOrr.png" type="image/png">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

        :root {{
            --yellow: #FFD700;
            --black: #000000;
            --dark-grey: #121212;
            --border-grey: #262626;
            --white: #FFFFFF;
            --text-muted: #A0A0A0;
            --font-main: 'Outfit', sans-serif;
            --font-accent: 'Space Grotesk', sans-serif;
        }}

        * {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: var(--font-main);
            background: var(--black);
            color: var(--white);
            margin: 0;
            line-height: 1.8;
        }}

        .product-highlight {{
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 215, 0, 0.05) 100%);
            border: 2px solid var(--yellow);
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
            position: relative;
            animation: highlightPulse 2s ease-in-out;
        }}

        @keyframes highlightPulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }}
            50% {{ box-shadow: 0 0 20px 5px rgba(255, 215, 0, 0.3); }}
        }}

        .product-badge {{
            position: absolute;
            top: -10px;
            right: 20px;
            background: var(--yellow);
            color: var(--black);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.875rem;
            z-index: 10;
        }}

        .buy-button {{
            background: var(--yellow);
            color: var(--black);
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1.1rem;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }}

        .buy-button:hover {{
            background: #FFC700;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 215, 0, 0.3);
        }}

        .product-info {{
            display: grid;
            grid-template-columns: 1fr 200px;
            gap: 2rem;
            align-items: center;
            margin: 1rem 0;
        }}

        .product-image {{
            width: 100%;
            max-width: 200px;
            height: 200px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .back-button {{
            background: var(--border-grey);
            color: var(--white);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }}

        .back-button:hover {{
            background: #333;
        }}
    </style>
</head>
<body>
    <div style="max-width: 800px; margin: 0 auto; padding: 2rem;">
        <a href="/home.html" class="back-button">← Back to Home</a>
        
        <div id="product-{product['asin']}" class="product-highlight">
            <div class="product-badge">FEATURED PRODUCT</div>
            
            <h1 style="font-size: 2rem; margin-bottom: 1rem; color: var(--yellow);">
                {product['title']}
            </h1>
            
            <div class="product-info">
                <div>
                    <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">
                        <strong>Price:</strong> {product.get('price', 'N/A')}
                    </p>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">
                        <strong>Category:</strong> {product.get('category', 'Tech')}
                    </p>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">
                        <strong>Rating:</strong> {product.get('rating', 'N/A')} ⭐
                    </p>
                </div>
                
                <div>
                    <img src="{product.get('image_url', '')}" alt="{product['title']}" class="product-image">
                </div>
            </div>
            
            <div style="text-align: center; margin: 2rem 0;">
                <a href="{product.get('affiliate_url', '')}" target="_blank" class="buy-button">
                    🔥 Get it Here - Limited Time Deal
                </a>
                <p style="margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted);">
                    ✅ Free shipping available<br>
                    ✅ 30-day money-back guarantee
                </p>
            </div>
        </div>
        
        <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--border-grey);">
            <h2 style="color: var(--yellow); margin-bottom: 1rem;">Product Details</h2>
            <p style="line-height: 1.6;">
                This amazing product is carefully selected by our team for its exceptional quality and value. 
                With thousands of satisfied customers, this item has become one of our top-selling products 
                in the {product.get('category', 'Tech')} category.
            </p>
        </div>
    </div>
    
    <script>
        // Smooth scroll to product when page loads with hash
        window.addEventListener('load', function() {{
            if (window.location.hash) {{
                const element = document.querySelector(window.location.hash);
                if (element) {{
                    setTimeout(function() {{
                        element.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'center'
                        }});
                    }}, 500);
                }}
            }}
        }});
        
        // Add some interactivity
        document.addEventListener('DOMContentLoaded', function() {{
            const buyButton = document.querySelector('.buy-button');
            if (buyButton) {{
                buyButton.addEventListener('click', function(e) {{
                    console.log('Product clicked: ' + JSON.stringify({{
                        product_id: '{product['asin']}', 
                        unique_id: '{unique_id}'
                    }}));
                }});
            }}
        }});
    </script>
</body>
</html>'''
    
    return html_content

def test_enhanced_links():
    """Test the enhanced link generation"""
    test_product = {
        'asin': 'B0FS74F9Q3',
        'title': 'FAHREN 2026 Upgraded Android Auto & CarPlay Wireless Adapter',
        'price': '$39.99',
        'category': 'Tech',
        'rating': '4.4',
        'image_url': 'https://m.media-amazon.com/images/I/61dtZM6FODL._AC_SL1500_.jpg',
        'affiliate_url': 'https://www.amazon.com/dp/B0FS74F9Q3?tag=amazingcoolfinds-20'
    }
    
    link_data = get_enhanced_website_link(test_product)
    
    print("🔗 ENHANCED WEBSITE LINK GENERATOR")
    print("=" * 50)
    print(f"Original ASIN: {test_product['asin']}")
    print(f"Unique ID: {link_data['unique_id']}")
    print(f"Enhanced Link: {link_data['link']}")
    print(f"Scroll Target: {link_data['scroll_target']}")
    print("=" * 50)
    
    # Test HTML generation
    html_content = create_enhanced_article_html(test_product)
    print(f"✅ Enhanced HTML generated: {len(html_content)} characters")
    
    return link_data

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 ENHANCED WEBSITE LINK GENERATOR")
    print("=" * 60)
    
    # Test enhanced links
    link_data = test_enhanced_links()
    
    print("\n📄 Enhanced pages would include:")
    print("   ✅ Smooth scroll animation")
    print("   ✅ Product highlighting")
    print("   ✅ Unique identifiers")
    print("   ✅ Enhanced product pages")
    print("   ✅ Direct affiliate links")