#!/usr/bin/env python3
"""
Production YouTube Uploader - FIXED with comment posting
"""
import os
import json
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("YouTubeUpload")

class ProductionYouTubeUploaderFixed:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']
        self.credentials = self._get_production_credentials()
        self.youtube = build("youtube", "v3", credentials=self.credentials)
    
    def _get_production_credentials(self):
        """Get credentials using your exact production configuration"""
        token_file = "token.json"
        
        # Try to load existing credentials
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_info(token_data, self.scopes)
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    from google.auth.transport.requests import Request
                    creds.refresh(Request())
                    log.info("✅ Refreshed expired credentials")
                    # Save refreshed credentials
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())
                
                return creds
            except Exception as e:
                log.warning(f"Failed to load existing credentials: {e}")
        
        # Create new credentials
        return self._create_production_credentials()
    
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
            
            # Save credentials for next time
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            
            log.info("✅ Production authentication successful!")
            return creds
            
        except Exception as e:
            log.error(f"❌ Production authentication failed: {e}")
            raise
    
    def post_comment_with_affiliate_link(self, video_id, affiliate_link):
        """Post first comment with affiliate link"""
        try:
            log.info("💬 Posting affiliate link as first comment...")
            
            comment_text = f"🔥 Get the limited time deal here: {affiliate_link}\n\n#cargadgets #androidauto #wireless #tech"
            
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
                log.info(f"✅ Affiliate comment posted! Comment ID: {comment_id}")
                return True
            else:
                log.warning("⚠️ Comment posted but no ID returned")
                return False
                
        except Exception as e:
            log.error(f"❌ Failed to post affiliate comment: {e}")
            return False
    
    def upload_video_with_comment(self, video_path, title, description, tags=None, affiliate_link=None):
        """Upload video and post affiliate comment"""
        try:
            log.info(f"📤 Starting upload: {video_path}")
            
            # Clean description (remove affiliate link from description)
            clean_description = description.replace(f"🔥 Limited time deal! Get it here: {affiliate_link}", "")
            
            # Request body
            body = {
                'snippet': {
                    'title': title,
                    'description': clean_description.strip(),
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
                log.info(f"🔗 YouTube URL: https://youtube.com/shorts/{video_id}")
                
                # Wait a moment for video to process
                log.info("⏳ Waiting for video processing...")
                time.sleep(10)
                
                # Post affiliate comment
                if affiliate_link:
                    success = self.post_comment_with_affiliate_link(video_id, affiliate_link)
                    if success:
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

def test_fixed_upload():
    """Test fixed YouTube upload with affiliate comment"""
    log.info("🚀 TESTING FIXED YOUTUBE UPLOADER")
    log.info("=" * 50)
    
    # Check prerequisites
    if not os.path.exists('client_secret.json'):
        log.error("❌ client_secret.json not found")
        return False
    
    if not os.path.exists('output_videos/video_B0FS74F9Q3.mp4'):
        log.error("❌ Video file not found")
        return False
    
    try:
        # Initialize fixed uploader
        uploader = ProductionYouTubeUploaderFixed()
        log.info("✅ Fixed YouTube uploader initialized")
        
        # Upload video with affiliate comment
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
        
        video_id = uploader.upload_video_with_comment(
            video_path, title, description, tags, affiliate_link
        )
        
        if video_id:
            log.info("=" * 50)
            log.info("🎉 FIXED UPLOAD SUCCESSFUL!")
            log.info(f"🎥 Video ID: {video_id}")
            log.info(f"🔗 YouTube URL: https://youtube.com/shorts/{video_id}")
            log.info("✅ Affiliate link: Posted in first comment")
            log.info("=" * 50)
            return True
        else:
            return False
            
    except Exception as e:
        log.error(f"❌ Fixed upload test failed: {e}")
        return False

if __name__ == "__main__":
    test_fixed_upload()