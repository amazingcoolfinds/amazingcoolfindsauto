#!/usr/bin/env python3
"""
YouTube Manual Auth - Copy paste method
"""
import os
import json
import pickle
from urllib.parse import parse_qs
from google_auth_oauthlib.flow import Flow

def manual_auth_process():
    """Step-by-step manual authentication"""
    
    # Load client secrets
    with open("client_secret.json", "r") as f:
        client_secrets = json.load(f)
    
    # Create flow with fixed redirect URI
    flow = Flow.from_client_config(
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
    
    print("🔐 MANUAL YOUTUBE AUTHENTICATION")
    print("=" * 60)
    print(f"1. Open URL in browser:")
    print(f"   {auth_url}")
    print()
    print("2. Accept permissions")
    print("3. Copy the FULL URL you're redirected to")
    print("4. I'll extract the code automatically")
    print()
    
    return flow

def process_callback_url(flow, callback_url):
    """Process the callback URL to get tokens"""
    try:
        # Extract code from URL
        if 'code=' in callback_url:
            # Parse URL to get authorization code
            parsed = parse_qs(callback_url.split('?')[1])
            auth_code = parsed.get('code', [None])[0]
            
            if auth_code:
                # Exchange code for tokens
                flow.fetch_token(code=auth_code)
                
                # Save credentials
                creds = flow.credentials
                with open("token.json", "wb") as token_file:
                    pickle.dump(creds, token_file)
                
                print(f"✅ Authentication successful!")
                print(f"📁 Token saved: token.json")
                print(f"🔑 Expires: {creds.expiry}")
                return creds
            else:
                print("❌ No authorization code found in URL")
                return None
        else:
            print("❌ Invalid callback URL format")
            return None
            
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        return None

def test_youtube_upload(creds):
    """Test actual YouTube upload"""
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    
    try:
        # Build service
        youtube = build("youtube", "v3", credentials=creds)
        print("✅ YouTube service built successfully!")
        
        # Upload test
        video_path = 'output_videos/video_B0FS74F9Q3.mp4'
        title = 'Upgrade Your Car with This Amazing Android Auto Adapter! 🚗'
        description = '''This incredible Android Auto adapter transforms your car in seconds!

✅ Wireless CarPlay & Android Auto
✅ Ultra-fast 5.8GHz WiFi connection  
✅ One-click multi-device switching
✅ Works with 2016+ car models

🔥 Get it here: https://www.amazon.com/dp/B0FS74F9Q3?tag=amazingcoolfinds-20

#cargadgets #androidauto #wireless #tech'''
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['cargadgets', 'androidauto', 'wireless', 'tech'],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        print("📤 Starting upload...")
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
            return True
        else:
            print("❌ Upload failed - no video ID")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 STEP 1: Generate authentication URL")
    flow = manual_auth_process()
    
    print("\n⏳ WAITING for you to complete browser authentication...")
    print("After you get redirected, copy the FULL URL and I'll process it.")
    
    # For demonstration, show what would happen
    print("\n📋 INSTRUCTIONS:")
    print("1. Open the URL above in your browser")
    print("2. Accept the YouTube permissions")  
    print("3. You'll be redirected to: http://localhost:8080/?code=...")
    print("4. Copy that ENTIRE URL")
    print("5. Run this script again with the URL as argument")
    print()
    print("🔗 Alternative: Use YouTube Studio manually for now")
    
    # Check if we already have valid token
    if os.path.exists("token.json"):
        print("📁 Testing existing token...")
        try:
            with open("token.json", "rb") as f:
                creds = pickle.load(f)
            
            if creds and creds.valid:
                success = test_youtube_upload(creds)
                if success:
                    print("🎉 EXISTING TOKEN WORKS!")
                else:
                    print("❌ Existing token failed")
            else:
                print("❌ Existing token invalid")
        except Exception as e:
            print(f"❌ Token error: {e}")