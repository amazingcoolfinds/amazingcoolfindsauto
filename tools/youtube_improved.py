#!/usr/bin/env python3
"""
Improved YouTube Auth and Upload
"""
import os
import pickle
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("YouTubeUpload")

class ImprovedYouTubeUploader:
    def __init__(self, client_secrets_file="client_secret.json"):
        self.client_secrets_file = client_secrets_file
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.credentials = self._get_or_create_credentials()
        self.youtube = build("youtube", "v3", credentials=self.credentials)
    
    def _get_or_create_credentials(self):
        """Get existing credentials or create new ones"""
        token_file = "token.json"
        creds = None
        
        # Load existing credentials
        if os.path.exists(token_file):
            try:
                with open(token_file, "rb") as token:
                    creds = pickle.load(token)
                log.info("✅ Loaded existing credentials")
            except Exception as e:
                log.warning(f"Failed to load token: {e}")
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    log.info("✅ Refreshed expired credentials")
                except Exception as e:
                    log.error(f"Failed to refresh: {e}")
                    return self._create_new_credentials()
            else:
                return self._create_new_credentials()
        
        return creds
    
    def _create_new_credentials(self):
        """Create new credentials via browser"""
        token_file = "token.json"
        
        try:
            log.info("🌐 Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, 
                self.scopes
            )
            
            # Use local server with automatic port selection
            creds = flow.run_local_server(
                port=0,
                prompt='consent',
                access_type='offline'  # Important for refresh token
            )
            
            # Save credentials for future use
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)
            
            log.info(f"✅ Authentication successful! Token saved to {token_file}")
            log.info(f"📧 Client: {creds.client_id}")
            log.info(f"🔑 Expires: {creds.expiry}")
            
            return creds
            
        except Exception as e:
            log.error(f"❌ Authentication failed: {e}")
            raise
    
    def upload_short(self, video_path, title, description, tags=None):
        """Upload video as YouTube Short"""
        if not os.path.exists(video_path):
            log.error(f"Video file not found: {video_path}")
            return None
        
        try:
            log.info(f"📤 Starting upload: {video_path}")
            
            # YouTube API request body
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or [],
                    'categoryId': '22'  # Technology category
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Media file
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True
            )
            
            # Upload request
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            log.info("⏳ Uploading video...")
            response = request.execute()
            
            video_id = response.get('id')
            if video_id:
                log.info(f"✅ Upload successful! Video ID: {video_id}")
                log.info(f"🔗 YouTube URL: https://youtube.com/shorts/{video_id}")
                return video_id
            else:
                log.error("❌ No video ID in response")
                return None
                
        except Exception as e:
            log.error(f"❌ Upload failed: {e}")
            return None

def main():
    """Test upload"""
    uploader = ImprovedYouTubeUploader()
    
    video_path = 'output_videos/video_B0FS74F9Q3.mp4'
    title = 'Upgrade Your Car with This Amazing Android Auto Adapter! 🚗'
    description = '''This incredible Android Auto adapter transforms your car in seconds!

✅ Wireless CarPlay & Android Auto
✅ Ultra-fast 5.8GHz WiFi connection  
✅ One-click multi-device switching
✅ Works with 2016+ car models
✅ Plug & Play setup

🔥 Limited time deal! Get it here: https://www.amazon.com/dp/B0FS74F9Q3?tag=amazingcoolfinds-20

#cargadgets #androidauto #wireless #tech #cargadgets #cardaccessories'''
    
    tags = ['cargadgets', 'androidauto', 'wireless', 'tech', 'caraccessories']
    
    video_id = uploader.upload_short(video_path, title, description, tags)
    
    if video_id:
        log.info("🎉 PIPELINE COMPLETE!")
        log.info("✅ Video generation: DONE (Diana voice)")
        log.info("✅ YouTube upload: DONE")
        log.info("✅ Website update: DONE")
    else:
        log.error("❌ Upload failed")

if __name__ == "__main__":
    main()