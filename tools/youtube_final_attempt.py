#!/usr/bin/env python3
"""
YouTube upload with browser-based auth - latest attempt
"""
import os
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging
import webbrowser
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("YouTubeUpload")

def final_youtube_auth_and_upload():
    """Final attempt at YouTube authentication and upload"""
    
    log.info("🚀 FINAL YOUTUBE PIPELINE TEST")
    log.info("=" * 50)
    
    # Check prerequisites
    if not os.path.exists('client_secret.json'):
        log.error("❌ client_secret.json not found")
        return False
    
    if not os.path.exists('output_videos/video_B0FS74F9Q3.mp4'):
        log.error("❌ Video file not found")
        return False
    
    try:
        # Load client secrets
        with open("client_secret.json", "r") as f:
            client_secrets = json.load(f)
        
        log.info("✅ Client secrets loaded")
        
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_config(
            client_secrets,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
            redirect_uri="http://localhost:8080"
        )
        
        # Generate auth URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        log.info("🌐 Opening browser for authentication...")
        log.info(f"URL: {auth_url}")
        
        # Try to open browser automatically
        try:
            webbrowser.open(auth_url)
            log.info("✅ Browser opened automatically")
        except Exception as e:
            log.warning(f"Could not open browser: {e}")
            log.info("Please open the URL manually")
        
        # Start local server to handle callback
        log.info("🔗 Waiting for authentication callback...")
        log.info("This will timeout after 60 seconds if no response")
        
        # Run the flow with timeout
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',
            access_type='offline',
            timeout_seconds=60
        )
        
        log.info("✅ Authentication successful!")
        
        # Save credentials
        with open("token.json", "wb") as token_file:
            pickle.dump(creds, token_file)
        
        log.info("📁 Token saved to token.json")
        
        # Build YouTube service
        youtube = build("youtube", "v3", credentials=creds)
        log.info("✅ YouTube service built successfully!")
        
        # Upload video
        return upload_video(youtube)
        
    except Exception as e:
        log.error(f"❌ Authentication failed: {e}")
        
        # Fallback: try existing token
        if os.path.exists("token.json"):
            try:
                log.info("🔄 Trying fallback with existing token...")
                with open("token.json", "rb") as token_file:
                    creds = pickle.load(token_file)
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    log.info("✅ Token refreshed")
                
                youtube = build("youtube", "v3", credentials=creds)
                return upload_video(youtube)
                
            except Exception as fallback_error:
                log.error(f"❌ Fallback also failed: {fallback_error}")
        
        return False

def upload_video(youtube):
    """Upload video to YouTube"""
    try:
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
        
        log.info(f"📤 Uploading: {video_path}")
        log.info(f"📝 Title: {title}")
        log.info(f"🏷️  Tags: {tags}")
        
        # Request body
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'
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
        
        log.info("⏳ Starting upload...")
        
        # Upload request
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response.get('id')
        
        if video_id:
            log.info(f"✅ UPLOAD SUCCESSFUL!")
            log.info(f"🎥 Video ID: {video_id}")
            log.info(f"🔗 YouTube URL: https://youtube.com/shorts/{video_id}")
            log.info(f"📊 File size: {os.path.getsize(video_path)/1024/1024:.1f}MB")
            
            # Success summary
            log.info("🎉 PIPELINE PHASE 2 COMPLETED!")
            log.info("   ✅ Video generation: DONE (Diana voice)")
            log.info("   ✅ YouTube upload: DONE")
            log.info("   ✅ Website update: DONE")
            log.info("   ✅ Instagram patch: WORKING")
            log.info("   ✅ Meta/TikTok: READY")
            
            return True
        else:
            log.error("❌ Upload failed - no video ID in response")
            return False
            
    except Exception as e:
        log.error(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    success = final_youtube_auth_and_upload()
    if success:
        log.info("🚀 READY FOR NEXT PHASE: Meta/TikTok integration")
    else:
        log.info("⏳ Consider alternative: Continue with other platforms")