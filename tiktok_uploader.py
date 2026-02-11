#!/usr/bin/env python3
import os
import json
import logging
import requests
from pathlib import Path

log = logging.getLogger("TikTokUploader")

class TikTokUploader:
    def __init__(self, token_file="tiktok_tokens.json"):
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.token_file = Path(token_file)
        self.access_token = self._load_tokens()
        
        if not self.client_key or not self.client_secret:
            log.warning("TikTok credentials missing in .env")

    def _load_tokens(self):
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                    return tokens.get('access_token')
            except:
                pass
        return None

    def upload_video(self, video_path: str, title: str):
        """Uploads a video to TikTok using the Video Kit API."""
        if not self.access_token:
            log.error("TikTok access token missing. Run manual auth first.")
            return None

        try:
            # 1. Initialize upload (Direct Post)
            url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            body = {
                "post_info": {
                    "title": title,
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_stitch": False,
                    "disable_comment": False,
                    "video_ad_tag": False
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": os.path.getsize(video_path),
                    "chunk_size": os.path.getsize(video_path),
                    "total_chunk_count": 1
                }
            }
            
            res = requests.post(url, headers=headers, json=body).json()
            if 'error' in res:
                log.error(f"TikTok Init failed: {res}")
                return None
                
            upload_url = res.get('data', {}).get('upload_url')
            if not upload_url:
                log.error(f"TikTok No upload URL: {res}")
                return None

            # 2. Upload the file
            with open(video_path, 'rb') as f:
                headers = {'Content-Type': 'video/mp4'}
                res = requests.put(upload_url, data=f, headers=headers)
                if res.status_code != 200:
                    log.error(f"TikTok Upload failed ({res.status_code}): {res.text}")
                    return None

            log.info(f"✅ Video uploaded to TikTok: {title}")
            return "SUCCESS" # TikTok V2 doesn't always return a public URL immediately
            
        except Exception as e:
            log.error(f"TikTok Error: {e}")
            return None

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    
    if args.test:
        uploader = TikTokUploader()
        if uploader.access_token:
            print(f"Token loaded: {uploader.access_token[:10]}...")
        else:
            print("❌ No token found. Create tiktok_tokens.json with {'access_token': '...'}")
