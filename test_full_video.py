#!/usr/bin/env python3
import json
import logging
from video_generator import VideoGenerator
from pipeline_scraper import ScriptGenerator

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FullTest")

def test():
    # 1. Select product
    product = {
        "asin": "B07C5NBXTD",
        "title": "Sooryehan Ginseng Skincare gift Set - Korean Skin Care Set for Intense Hydration",
        "price": "$95.00",
        "rating": "4.5",
        "image_url": "https://m.media-amazon.com/images/I/71htn4SLjML._AC_SL1500_.jpg",
    }
    
    # 2. Generate script
    print("🤖 Generating Script...")
    scripts = ScriptGenerator()
    script = scripts.generate(product)
    print(json.dumps(script, indent=2))
    
    # 3. Generate video
    print("🎬 Generating Video...")
    gen = VideoGenerator()
    video_path = gen.generate(product, script)
    
    if video_path:
        print(f"✨ SUCCESS! Video created at: {video_path}")
    else:
        print("❌ FAILED to create video.")

if __name__ == "__main__":
    test()
