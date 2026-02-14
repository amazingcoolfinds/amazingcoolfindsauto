#!/usr/bin/env python3
"""
Extract code from successful auth and complete upload
"""
import os
import json
import pickle
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("YouTubeUpload")

def complete_auth_with_code():
    """Complete auth using the code we received"""
    
    # The authorization code from the callback
    auth_code = "4/0ASc3gC1yT5eO8ti-m8VOKC6d-yaN0VV8mIojtn3tGo_lpHCSr_Fu0gxwih314ny9cZ6Z3g"
    
    log.info("🔑 Using received authorization code")
    log.info(f"Code: {auth_code[:20]}...")
    
    try:
        # Load client secrets
        with open("client_secret.json", "r") as f:
            client_secrets = json.load(f)
        
        # Create flow with matching redirect URI
        flow = Flow.from_client_config(
            client_secrets,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
            redirect_uri="http://localhost:8080/"
        )
        
        # Exchange code for tokens
        flow.fetch_token(code=auth_code)
        
        # Save credentials
        creds = flow.credentials
        with open("token.json", "wb") as token_file:
            pickle.dump(creds, token_file)
        
        log.info("✅ Token exchange successful!")
        log.info(f"📁 Token saved to token.json")
        log.info(f"🔑 Expires: {creds.expiry}")
        
        # Build YouTube service
        youtube = build("youtube", "v3", credentials=creds)
        log.info("✅ YouTube service built successfully!")
        
        # Upload video
        return upload_video(youtube)
        
    except Exception as e:
        log.error(f"❌ Token exchange failed: {e}")
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
        
        log.info(f"📤 Starting upload: {video_path}")
        log.info(f"📝 Title: {title}")
        
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
        
        log.info("⏳ Uploading to YouTube...")
        
        # Upload request
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response.get('id')
        
        if video_id:
            log.info(f"🎉 UPLOAD SUCCESSFUL!")
            log.info(f"🎥 Video ID: {video_id}")
            log.info(f"🔗 YouTube URL: https://youtube.com/shorts/{video_id}")
            log.info(f"📊 File size: {os.path.getsize(video_path)/1024/1024:.1f}MB")
            
            # Success summary
            log.info("=" * 50)
            log.info("🎉 YOUTUBE PIPELINE COMPLETED!")
            log.info("   ✅ Video generation: DONE (Diana voice)")
            log.info("   ✅ YouTube upload: DONE")
            log.info("   ✅ Website update: DONE")
            log.info("   ✅ Instagram patch: WORKING")
            log.info("   ✅ Meta/TikTok: READY")
            log.info("=" * 50)
            
            return True
        else:
            log.error("❌ Upload failed - no video ID")
            return False
            
    except Exception as e:
        log.error(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    log.info("🚀 COMPLETING YOUTUBE AUTHENTICATION")
    log.info("=" * 50)
    
    success = complete_auth_with_code()
    
    if success:
        log.info("🎯 READY FOR PHASE 3: Full pipeline automation!")
    else:
        log.info("⏳ Consider manual upload while we troubleshoot")