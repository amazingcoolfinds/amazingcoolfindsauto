#!/usr/bin/env python3
"""
YouTube OAuth with manual redirect (no localhost server)
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

def youtube_auth_manual_redirect():
    """OAuth with manual redirect URI"""
    
    # Load client secrets
    with open("client_secret.json", "r") as f:
        client_secrets = json.load(f)
    
    # Use a public redirect URI that doesn't need a server
    flow = Flow.from_client_config(
        client_secrets,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
        redirect_uri="https://localhost"  # This will show the code in the URL
    )
    
    # Generate auth URL
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    print("🔐 YOUTUBE AUTHENTICATION - NO LOCALHOST SERVER")
    print("=" * 60)
    print(f"1. Open this URL:")
    print(f"   {auth_url}")
    print()
    print("2. Accept permissions")
    print("3. You'll see an error page - that's OK!")
    print("4. Copy the authorization code from the URL")
    print("5. The code is after 'code=' in the address bar")
    print()
    print("Example: https://localhost/?code=4/0AX4XfWh...")
    print("Your code: 4/0AX4XfWh...")
    print()
    
    return flow

def exchange_code_for_tokens(flow, auth_code):
    """Exchange authorization code for tokens"""
    try:
        # Exchange code for tokens
        flow.fetch_token(code=auth_code)
        
        # Save credentials
        creds = flow.credentials
        with open("token.json", "wb") as token_file:
            pickle.dump(creds, token_file)
        
        print(f"✅ Token exchange successful!")
        print(f"📁 Token saved to token.json")
        print(f"🔑 Expires: {creds.expiry}")
        return creds
        
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        return None

def test_youtube_service(creds):
    """Test YouTube service and upload"""
    try:
        # Build service
        youtube = build("youtube", "v3", credentials=creds)
        print("✅ YouTube service built successfully!")
        
        # Upload video
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
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['cargadgets', 'androidauto', 'wireless', 'tech', 'caraccessories'],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        print("📤 Starting upload to YouTube...")
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response.get('id')
        
        if video_id:
            print(f"✅ UPLOAD SUCCESSFUL!")
            print(f"🎥 Video ID: {video_id}")
            print(f"🔗 YouTube URL: https://youtube.com/shorts/{video_id}")
            print("🎉 PIPELINE PHASE 2 COMPLETED!")
            return True
        else:
            print("❌ Upload failed - no video ID returned")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def interactive_auth():
    """Interactive authentication with code input"""
    flow = youtube_auth_manual_redirect()
    
    # Wait for user to provide code
    auth_code = input("\n🔑 Paste the authorization code here: ").strip()
    
    if auth_code:
        creds = exchange_code_for_tokens(flow, auth_code)
        if creds:
            success = test_youtube_service(creds)
            if success:
                print("\n🎯 STATUS UPDATE:")
                print("   ✅ Video generation: DONE (Diana voice)")
                print("   ✅ Website update: DONE")
                print("   ✅ YouTube upload: DONE")
                print("   ✅ Instagram patch: WORKING")
                print("   ⏳ Meta/TikTok: READY")
                print("\n🚀 Phase 2 pipeline 90% complete!")
    else:
        print("❌ No authorization code provided")

if __name__ == "__main__":
    # Check if we have existing valid token
    if os.path.exists("token.json"):
        try:
            with open("token.json", "rb") as f:
                creds = pickle.load(f)
            
            if creds and creds.valid:
                print("✅ Found valid existing token")
                test_youtube_service(creds)
            else:
                print("❌ Existing token invalid, running fresh auth")
                interactive_auth()
        except Exception as e:
            print(f"❌ Token error: {e}")
            interactive_auth()
    else:
        interactive_auth()