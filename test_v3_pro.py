#!/usr/bin/env python3
import json
import logging
from pathlib import Path
from pipeline_scraper import AmazonFetcher, ScriptGenerator, BASE_WEBSITE_URL
from video_generator import VideoGenerator
from voice_generator import VoiceGenerator
from youtube_uploader import YouTubeUploader

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("PRO_TEST")

def test_v3():
    # 1. Fetch Enrichment
    print("🔍 Fetching high-end product with multi-images...")
    amazon = AmazonFetcher()
    products = amazon.search("luxury designer watch", count=1)
    
    if not products:
        print("❌ No products found.")
        return
        
    product = products[0]
    print(f"✅ Found: {product['title']}")
    print(f"✅ Images: {len(product.get('images', []))}")
    
    # 2. Script
    print("🤖 Generating professional narration script...")
    scripts = ScriptGenerator()
    script = scripts.generate(product)
    print(json.dumps(script, indent=2))
    
    # 3. Voice
    print("🎙️ Generating Nova voiceover...")
    voice_gen = VoiceGenerator()
    voice_path = voice_gen.generate(script['narration'], product['asin'])
    
    # 4. Video Carousel
    print("🎬 Assembling Carousel Video (15s)...")
    video_gen = VideoGenerator()
    video_path = video_gen.generate(product, script, voice_path=voice_path)
    
    if video_path:
        print(f"🏆 SUCCESS! Pro Video at: {video_path}")
        
        # 5. YouTube Upload
        try:
            print("📤 Starting YouTube upload...")
            uploader = YouTubeUploader()
            web_link = f"{BASE_WEBSITE_URL}/#{product['asin']}"
            description = f"{script['narration']}\n\n🔥 Get it here: {web_link}\n\n#amazondeals #luxury #shopping"
            
            yt_url = uploader.upload_short(
                video_path=video_path,
                title=script['title'],
                description=description,
                tags=script['hashtags']
            )
            if yt_url:
                print(f"✅ Video LIVE on YouTube: {yt_url}")
                product['youtube_url'] = yt_url
                
                # 6. Save to products.json
                try:
                    data_dir = Path(__file__).parent / "data"
                    products_file = data_dir / "products.json"
                    
                    current_products = []
                    if products_file.exists():
                        with open(products_file, 'r', encoding='utf-8') as f:
                            current_products = json.load(f)
                    
                    # Check if exists
                    exists = False
                    for p in current_products:
                        if p['asin'] == product['asin']:
                            p.update(product)
                            exists = True
                            break
                    
                    if not exists:
                        current_products.append(product)
                        
                    with open(products_file, 'w', encoding='utf-8') as f:
                        json.dump(current_products, f, indent=2, ensure_ascii=False)
                    print(f"✅ Product saved to {products_file}")
                    
                except Exception as e:
                    print(f"❌ Failed to save to products.json: {e}")

        except Exception as e:
            print(f"❌ YouTube upload failed: {e}")
    else:
        print("❌ Video assembly failed.")

if __name__ == "__main__":
    test_v3()
