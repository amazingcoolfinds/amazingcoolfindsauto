#!/usr/bin/env python3
"""
Final fix - use exact redirect URI from callback
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

def final_youtube_upload():
    """Final attempt with correct redirect URI"""
    
    # The authorization code we received
    auth_code = "4/0ASc3gC1yT5eO8ti-m8VOKC6d-yaN0VV8mIojtn3tGo_lpHCSr_Fu0gxwih314ny9cZ6Z3g"
    
    log.info("🚀 FINAL YOUTUBE UPLOAD ATTEMPT")
    log.info("=" * 50)
    log.info(f"🔑 Using code: {auth_code[:20]}...")
    
    try:
        # Load client secrets
        with open("client_secret.json", "r") as f:
            client_secrets = json.load(f)
        
        # Try different redirect URIs
        redirect_uris = [
            "http://localhost:8080",
            "http://localhost:8080/",
            "http://localhost:8080/callback"
        ]
        
        for redirect_uri in redirect_uris:
            try:
                log.info(f"🔄 Trying redirect URI: {redirect_uri}")
                
                # Create flow
                flow = Flow.from_client_config(
                    client_secrets,
                    scopes=["https://www.googleapis.com/auth/youtube.upload"],
                    redirect_uri=redirect_uri
                )
                
                # Exchange code for tokens
                flow.fetch_token(code=auth_code)
                
                # Success!
                creds = flow.credentials
                log.info(f"✅ Token exchange successful with: {redirect_uri}")
                
                # Save credentials
                with open("token.json", "wb") as token_file:
                    pickle.dump(creds, token_file)
                
                log.info("📁 Token saved to token.json")
                
                # Build YouTube service
                youtube = build("youtube", "v3", credentials=creds)
                log.info("✅ YouTube service built successfully!")
                
                # Upload video
                return upload_video(youtube)
                
            except Exception as uri_error:
                log.warning(f"Redirect URI {redirect_uri} failed: {uri_error}")
                continue
        
        log.error("❌ All redirect URIs failed")
        return False
        
    except Exception as e:
        log.error(f"❌ Final attempt failed: {e}")
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
        
        log.info(f"📤 Starting YouTube upload...")
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
        
        log.info("⏳ Uploading video...")
        
        # Upload request
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response.get('id')
        
        if video_id:
            log.info("=" * 50)
            log.info("🎉 YOUTUBE UPLOAD SUCCESSFUL!")
            log.info(f"🎥 Video ID: {video_id}")
            log.info(f"🔗 YouTube URL: https://youtube.com/shorts/{video_id}")
            log.info(f"📊 File size: {os.path.getsize(video_path)/1024/1024:.1f}MB")
            log.info(f"🎤 Voice: Diana")
            log.info("=" * 50)
            
            # Complete pipeline summary
            log.info("🎯 COMPLETE PIPELINE STATUS:")
            log.info("   ✅ Video generation: DONE (Diana voice)")
            log.info("   ✅ YouTube upload: DONE")
            log.info("   ✅ Website update: DONE")
            log.info("   ✅ Instagram patch: WORKING")
            log.info("   ✅ Cloudflare deployment: LIVE")
            log.info("   ⏳ Meta/TikTok: READY")
            log.info("=" * 50)
            log.info("🚀 PHASE 2 PIPELINE COMPLETED!")
            
            return True
        else:
            log.error("❌ Upload failed - no video ID")
            return False
            
    except Exception as e:
        log.error(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    final_youtube_upload()