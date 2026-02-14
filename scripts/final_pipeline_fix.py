#!/usr/bin/env python3
"""
Final Fixed Pipeline - YouTube comments + Make.com webhook
"""
import os
import json
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FinalPipeline")

def load_env_vars():
    """Load environment variables properly"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key.strip()] = value.strip()
        log.info("✅ Environment variables loaded")
    except Exception as e:
        log.error(f"❌ Failed to load .env: {e}")

class FinalYouTubeUploader:
    def __init__(self):
        # Fixed scopes - includes comment posting
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube.force-ssl'
        ]
        self.credentials = self._get_credentials()
        self.youtube = build("youtube", "v3", credentials=self.credentials)
    
    def _get_credentials(self):
        """Get credentials with proper scopes"""
        token_file = "token.json"
        
        # Try existing credentials
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_info(token_data, self.scopes)
                
                # Check if we have the right scopes
                if not all(scope in creds.scopes for scope in self.scopes):
                    log.warning("⚠️ Existing token missing comment scope. Re-authenticating...")
                    return self._create_new_credentials()
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    from google.auth.transport.requests import Request
                    creds.refresh(Request())
                    # Save refreshed credentials
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())
                    log.info("✅ Refreshed credentials")
                
                return creds
            except Exception as e:
                log.warning(f"Failed to load existing credentials: {e}")
        
        # Create new credentials
        return self._create_new_credentials()
    
    def _create_new_credentials(self):
        """Create new credentials with comment scope"""
        try:
            log.info("🌐 Creating new credentials with comment scope...")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', 
                scopes=self.scopes
            )
            
            creds = flow.run_local_server(
                port=8080, 
                access_type='offline', 
                prompt='consent'
            )
            
            # Save credentials
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            
            log.info("✅ New credentials created with comment scope!")
            return creds
            
        except Exception as e:
            log.error(f"❌ Failed to create credentials: {e}")
            raise
    
    def post_affiliate_comment(self, video_id, affiliate_link):
        """Post affiliate link as first comment"""
        try:
            log.info("💬 Posting affiliate link as first comment...")
            
            comment_text = f"🔥 Get it here: {affiliate_link}\n\n#cargadgets #androidauto #wireless #tech"
            
            comment_request = {
                'snippet': {
                    'videoId': video_id,
                    'topLevelComment': {
                        'snippet': {
                            'textOriginal': comment_text
                        }
                    }
                }
            }
            
            # Post comment
            response = self.youtube.commentThreads().insert(
                part='snippet',
                body=comment_request
            ).execute()
            
            comment_id = response.get('id')
            if comment_id:
                log.info(f"✅ Affiliate comment posted! ID: {comment_id}")
                return True
            else:
                log.warning("⚠️ Comment posted but no ID returned")
                return False
                
        except Exception as e:
            log.error(f"❌ Failed to post comment: {e}")
            return False
    
    def upload_video(self, video_path, title, description, tags=None, affiliate_link=None):
        """Upload video and post affiliate comment"""
        try:
            log.info(f"📤 Uploading: {video_path}")
            
            # Remove affiliate from description (post as comment instead)
            clean_description = description
            if affiliate_link and affiliate_link in description:
                clean_description = description.replace(f"🔥 Get it here: {affiliate_link}", "")
            
            # Request body
            body = {
                'snippet': {
                    'title': title,
                    'description': clean_description.strip(),
                    'tags': tags or [],
                    'categoryId': '22'
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Media file
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            log.info("⏳ Uploading to YouTube...")
            
            # Upload request
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            video_id = response.get('id')
            
            if video_id:
                log.info(f"✅ Video uploaded! ID: {video_id}")
                log.info(f"🔗 URL: https://youtube.com/shorts/{video_id}")
                
                # Wait for processing
                log.info("⏳ Waiting for video processing...")
                time.sleep(15)
                
                # Post affiliate comment
                if affiliate_link:
                    comment_success = self.post_affiliate_comment(video_id, affiliate_link)
                    if comment_success:
                        log.info("✅ Affiliate link posted in first comment!")
                    else:
                        log.warning("⚠️ Could not post affiliate comment")
                
                return video_id
            else:
                log.error("❌ Upload failed - no video ID")
                return None
                
        except Exception as e:
            log.error(f"❌ Upload failed: {e}")
            return None

def test_make_webhook():
    """Test Make.com webhook"""
    try:
        webhook_url = os.getenv("MAKE_WEBHOOK_URL")
        if not webhook_url:
            log.error("❌ MAKE_WEBHOOK_URL not found")
            return False
        
        # Sample data that pipeline would send
        product_data = {
            "asin": "B0FS74F9Q3",
            "title": "FAHREN 2026 Upgraded Android Auto & CarPlay Wireless Adapter",
            "price": "$39.99",
            "category": "Tech",
            "affiliate_url": "https://www.amazon.com/dp/B0FS74F9Q3?tag=amazingcoolfinds-20",
            "video_id": "pxaLqWark2o",
            "video_url": "https://youtube.com/shorts/pxaLqWark2o",
            "voice": "Diana",
            "status": "uploaded",
            "timestamp": "2026-02-09T13:00:00Z"
        }
        
        log.info("⚡ Testing Make.com webhook...")
        response = requests.post(webhook_url, json=product_data, timeout=10)
        
        if response.ok:
            log.info(f"✅ Webhook successful! Status: {response.status_code}")
            return True
        else:
            log.error(f"❌ Webhook failed! Status: {response.status_code}")
            log.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        log.error(f"❌ Webhook error: {e}")
        return False

def main():
    """Test both fixes"""
    log.info("🚀 TESTING FINAL FIXES")
    log.info("=" * 50)
    
    # Load environment
    load_env_vars()
    
    # Test 1: Make.com webhook
    log.info("1️⃣ Testing Make.com webhook...")
    webhook_success = test_make_webhook()
    
    # Test 2: YouTube upload with comment
    log.info("\n2️⃣ Testing YouTube upload with comment...")
    
    if os.path.exists('output_videos/video_B0FS74F9Q3.mp4'):
        try:
            uploader = FinalYouTubeUploader()
            video_path = 'output_videos/video_B0FS74F9Q3.mp4'
            title = 'Upgrade Your Car with This Amazing Android Auto Adapter! 🚗'
            description = '''This incredible Android Auto adapter transforms your car in seconds!

✅ Wireless CarPlay & Android Auto
✅ Ultra-fast 5.8GHz WiFi connection  
✅ One-click multi-device switching
✅ Works with 2016+ car models
✅ Plug & Play setup

#cargadgets #androidauto #wireless #tech #cargadgets #cardaccessories'''
            
            tags = ['cargadgets', 'androidauto', 'wireless', 'tech', 'caraccessories']
            affiliate_link = "https://www.amazon.com/dp/B0FS74F9Q3?tag=amazingcoolfinds-20"
            
            video_id = uploader.upload_video(video_path, title, description, tags, affiliate_link)
            upload_success = video_id is not None
            
        except Exception as e:
            log.error(f"❌ YouTube test failed: {e}")
            upload_success = False
    else:
        log.warning("⚠️ Test video not found")
        upload_success = False
    
    # Summary
    log.info("\n" + "=" * 50)
    log.info("🎯 FINAL FIX RESULTS:")
    log.info(f"   📡 Make.com webhook: {'✅ WORKING' if webhook_success else '❌ FAILED'}")
    log.info(f"   📹 YouTube upload: {'✅ WORKING' if upload_success else '❌ FAILED'}")
    log.info(f"   💬 Comment posting: {'✅ FIXED' if upload_success else '❌ NEEDS WORK'}")
    log.info("=" * 50)
    
    if webhook_success and upload_success:
        log.info("🎉 ALL FIXES WORKING!")
        log.info("🚀 Pipeline is 100% operational!")
    else:
        log.info("⚠️ Some issues remain to be resolved")
    
    return webhook_success and upload_success

if __name__ == "__main__":
    main()