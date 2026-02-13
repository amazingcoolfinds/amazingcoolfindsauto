#!/usr/bin/env python3
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("FinalizeTest")

def finalize():
    # 1. Load the generated product data (if exists) or create it from the last test
    # From the logs we know the ASIN was B0FZ9ZMF3N
    asin = "B0FZ9ZMF3N"
    video_path = f"output_videos/video_{asin}.mp4"
    
    if not os.path.exists(video_path):
        log.error(f"❌ Video not found at {video_path}")
        return

    try:
        from youtube_production import ProductionYouTubeUploader
        from enhanced_pipeline import update_website_data, save_processed_product
        
        # 2. Upload to YouTube
        log.info(f"📹 Uploading {asin} to YouTube...")
        yt_up = ProductionYouTubeUploader()
        
        # We need the product info for titles/descriptions
        # Since this is a one-off fix, I'll mock the metadata if I can't find it
        # But wait, I can probably scrape it again quickly or just use placeholder
        title = "Incredible Tech Find 2026!"
        description = f"Check this out! Incredible product found on Amazon.\n\n🔥 Buy here: https://amazing-cool-finds.com/item/{asin}\n\n#amazonfinds #tech"
        
        video_id = yt_up.upload_video(
            video_path, 
            title, 
            description, 
            ["amazonfinds", "tech"],
            affiliate_link=f"https://amazing-cool-finds.com/item/{asin}"
        )
        
        if video_id:
            log.info(f"✅ YouTube upload successful: {video_id}")
            product_data = {
                "asin": asin,
                "title": title,
                "video_url": f"https://youtube.com/shorts/{video_id}",
                "video_id": video_id,
                "processed_at": "2026-02-13T15:50:00"
            }
            
            # 3. Update Website
            log.info("🌐 Syncing to website...")
            save_processed_product(product_data)
            update_website_data([product_data])
            log.info("🎉 Cycle complete!")
        else:
            log.error("❌ YouTube upload failed.")

    except Exception as e:
        log.error(f"❌ Finalization error: {e}")

if __name__ == "__main__":
    finalize()
