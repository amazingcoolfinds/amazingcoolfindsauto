#!/usr/bin/env python3
"""
Production YouTube Uploader - Using your exact configuration
"""
import os
import json
import pickle
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging
import base64

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("YouTubeUpload")

class ProductionYouTubeUploader:
    def __init__(self):
        # Added force-ssl for comment posting
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube.force-ssl'
        ]
        self.credentials = self._get_production_credentials()
        self.youtube = build("youtube", "v3", credentials=self.credentials)
    
    def _get_production_credentials(self):
        """Get credentials from Env Vars (CI) or Local Files"""
        token_file = "token.json"
        
        # 1. Try Loading from Environment Variables (Priority for GitHub Actions)
        token_b64 = os.getenv("YT_TOKEN_BASE64")
        secret_b64 = os.getenv("YT_CLIENT_SECRET_BASE64")
        
        if token_b64 and secret_b64:
            from google.oauth2.credentials import Credentials
            try:
                log.info("🔐 Loading YouTube credentials from Environment Variables...")
                token_data = json.loads(base64.b64decode(token_b64).decode('utf-8'))
                creds = Credentials.from_authorized_user_info(token_data, self.scopes)
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    log.info("✅ Refreshed environment credentials")
                
                return creds
            except Exception as e:
                log.error(f"❌ Failed to load credentials from Env: {e}")

        # 2. Try to load existing local credentials
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                
                # Handle both pickle and JSON formats
                if isinstance(token_data, dict):
                    from google.oauth2.credentials import Credentials
                    creds = Credentials.from_authorized_user_info(token_data, self.scopes)
                else:
                    # Handle pickle format
                    with open(token_file, 'rb') as f:
                        creds = pickle.load(f)
                
                # Check if we have the right scopes
                if not all(scope in creds.scopes for scope in self.scopes):
                    log.warning("⚠️ Existing token missing required scopes. Re-authenticating...")
                    return self._create_production_credentials()
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    log.info("✅ Refreshed expired credentials")
                    # Save refreshed credentials
                    self._save_credentials(creds)
                
                return creds
            except Exception as e:
                log.warning(f"Failed to load existing credentials: {e}")
        
        # If no credentials found and we aren't in a position to run a local server, return None
        # In a real CI or background task, we don't want to block here.
        log.warning("⚠️ No valid YouTube credentials found and cannot start interactive auth. Skipping.")
        return None
    
    def _create_production_credentials(self):
        """Create new credentials using your exact configuration"""
        try:
            log.info("🌐 Starting production authentication...")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', 
                scopes=self.scopes
            )
            
            creds = flow.run_local_server(
                port=8080, 
                access_type='offline', 
                prompt='consent'
            )
            
            # Save the credentials
            self._save_credentials(creds)
            
            log.info("✅ Production authentication successful!")
            return creds
            
        except Exception as e:
            log.error(f"❌ Production authentication failed: {e}")
            raise
    
    def _save_credentials(self, creds):
        """Save credentials using your exact method"""
        try:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            with open('token.json', 'wb') as token_file:
                pickle.dump(creds, token_file)

    def post_affiliate_comment(self, video_id, affiliate_link):
        """Post affiliate link as first comment"""
        try:
            log.info("💬 Posting affiliate link as first comment...")
            
            comment_text = f"🔥 Get it here: {affiliate_link}\n\n#coolfinds #amazonfinds #techdeals"
            
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
        """Upload video to YouTube and post affiliate comment"""
        try:
            log.info(f"📤 Starting production upload: {video_path}")
            
            # Request body
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or [],
                    'categoryId': '22'  # Technology
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
            
            log.info("⏳ Uploading to YouTube...")
            
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            video_id = response.get('id')
            
            if video_id:
                log.info(f"✅ Upload successful! ID: {video_id}")
                
                if affiliate_link:
                    log.info("⏳ Waiting for video processing (15s) for comment...")
                    time.sleep(15)
                    self.post_affiliate_comment(video_id, affiliate_link)
                
                return video_id
            else:
                log.error("❌ Upload failed - no video ID")
                return None
                
        except Exception as e:
            log.error(f"❌ Upload failed: {e}")
            return None

if __name__ == "__main__":
    # Test script logic
    pass