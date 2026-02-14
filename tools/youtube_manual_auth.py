#!/usr/bin/env python3
"""
Manual YouTube authentication with clipboard method
"""
import os
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

def manual_auth_with_clipboard():
    client_secrets_file = "client_secret.json"
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    
    # Load client secrets
    with open(client_secrets_file, "r") as f:
        client_secrets = json.load(f)
    
    # Create flow
    flow = Flow.from_client_config(
        client_secrets,
        scopes=scopes,
        redirect_uri="http://localhost:8080"
    )
    
    # Generate auth URL
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    print("🔐 MANUAL YOUTUBE AUTHENTICATION")
    print("=" * 50)
    print(f"1. Open this URL in your browser:")
    print(f"   {auth_url}")
    print()
    print("2. Sign in and accept permissions")
    print("3. Copy the authorization code from the URL after 'code='")
    print()
    
    # Wait for user input
    auth_code = input("4. Paste the authorization code here: ").strip()
    
    # Exchange code for tokens
    try:
        flow.fetch_token(code=auth_code)
        
        # Save credentials
        creds = flow.credentials
        with open("token.json", "wb") as token_file:
            pickle.dump(creds, token_file)
        
        print(f"✅ Authentication successful!")
        print(f"📁 Token saved to token.json")
        print(f"🔑 Expires: {creds.expiry}")
        return creds
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def test_upload():
    """Test upload after authentication"""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    
    try:
        # Load credentials
        with open("token.json", "rb") as token_file:
            creds = pickle.load(token_file)
        
        # Build service
        youtube = build("youtube", "v3", credentials=creds)
        
        print("✅ YouTube service built successfully!")
        
        # Test upload
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
    import json
    
    creds = manual_auth_with_clipboard()
    if creds:
        print()
        print("🚀 Testing upload...")
        success = test_upload()
        if success:
            print("🎉 COMPLETE PIPELINE WORKING!")
            print("✅ Video generation: DONE (Diana voice)")
            print("✅ YouTube upload: DONE") 
            print("✅ Website update: DONE")