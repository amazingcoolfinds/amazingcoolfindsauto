#!/usr/bin/env python3
import os
import time
import requests
import logging
from pathlib import Path

log = logging.getLogger("MetaUploader")

class MetaUploader:
    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.ig_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        
        if not all([self.access_token, self.page_id, self.ig_account_id]):
            log.warning("Meta credentials missing in .env")

    def upload_to_facebook(self, video_path: str, caption: str):
        """Uploads a Reel to a Facebook Page using the rupload flow."""
        try:
            url = f"https://graph.facebook.com/v19.0/{self.page_id}/video_reels"
            # 1. Initialize upload
            payload = {
                'upload_phase': 'start',
                'access_token': self.access_token
            }
            res = requests.post(url, data=payload).json()
            video_id = res.get('video_id')
            if not video_id:
                log.error(f"FB Init failed: {res}")
                return None

            # 2. Upload video file
            file_size = os.path.getsize(video_path)
            with open(video_path, 'rb') as f:
                headers = {
                    'Authorization': f'OAuth {self.access_token}',
                    'offset': '0',
                    'file_size': str(file_size),
                    'Content-Type': 'application/octet-stream'
                }
                upload_url = f"https://rupload.facebook.com/video-reels/{video_id}"
                res = requests.post(upload_url, data=f, headers=headers).json()
                if not res.get('success'):
                    log.error(f"FB Upload failed: {res}")
                    return None

            # 3. Publish
            publish_url = f"https://graph.facebook.com/v19.0/{self.page_id}/video_reels"
            publish_payload = {
                'upload_phase': 'finish',
                'video_id': video_id,
                'video_state': 'PUBLISHED',
                'description': caption,
                'access_token': self.access_token
            }
            res = requests.post(publish_url, data=publish_payload).json()
            if res.get('success'):
                log.info(f"✅ Reel published to FB Page: {video_id}")
                return video_id
            log.error(f"FB Publish failed: {res}")
            return None
        except Exception as e:
            log.error(f"FB Error: {e}")
            return None

    def upload_to_instagram(self, video_path: str, caption: str):
        """Uploads a Reel to Instagram Business using public URL flow."""
        try:
            # 1. Get public URL (Instagram requires a public URL to fetch the video)
            public_url = self._get_public_url(video_path)
            if not public_url:
                return None

            # 2. Create media container
            url = f"https://graph.facebook.com/v19.0/{self.ig_account_id}/media"
            payload = {
                'media_type': 'REELS',
                'video_url': public_url,
                'caption': caption,
                'access_token': self.access_token
            }
            res = requests.post(url, data=payload).json()
            creation_id = res.get('id')
            if not creation_id:
                log.error(f"IG container failed: {res}")
                return None

            # 3. Wait for processing
            log.info("⏳ Waiting for IG processing...")
            status_url = f"https://graph.facebook.com/v19.0/{creation_id}"
            params = {'fields': 'status_code', 'access_token': self.access_token}
            for _ in range(10):
                time.sleep(10)
                status = requests.get(status_url, params=params).json()
                if status.get('status_code') == 'FINISHED':
                    break
                log.info(f"   Status: {status.get('status_code')}")
            else:
                log.error("IG processing timed out")
                return None

            # 4. Publish
            publish_url = f"https://graph.facebook.com/v19.0/{self.ig_account_id}/media_publish"
            publish_payload = {
                'creation_id': creation_id,
                'access_token': self.access_token
            }
            res = requests.post(publish_url, data=publish_payload).json()
            if res.get('id'):
                log.info(f"✅ Reel published to IG: {res['id']}")
                return res['id']
            log.error(f"IG Publish failed: {res}")
            return None
        except Exception as e:
            log.error(f"IG Error: {e}")
            return None

    def _get_public_url(self, video_path: str) -> str:
        """Uploads video to Catbox.moe for a temporary public URL."""
        try:
            log.info("☁️ Uploading to Catbox for public URL...")
            url = "https://catbox.moe/user/api.php"
            with open(video_path, 'rb') as f:
                res = requests.post(url, data={'reqtype': 'fileupload'}, files={'fileToUpload': f}, timeout=30)
                if res.status_code == 200:
                    public_url = res.text.strip()
                    log.info(f"   Public URL: {public_url}")
                    return public_url
            log.error(f"Catbox upload failed: {res.text}")
            return None
        except Exception as e:
            log.error(f"Public URL error: {e}")
            return None

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    
    if args.test:
        # Diagnostic mode
        uploader = MetaUploader()
        print(f"Token: {uploader.access_token[:10]}...")
        print(f"Page ID: {uploader.page_id}")
        print(f"IG ID: {uploader.ig_account_id}")
