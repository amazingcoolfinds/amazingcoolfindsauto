#!/usr/bin/env python3
"""
Manual YouTube authentication script
"""
import os
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def manual_auth():
    client_secrets_file = "client_secret.json"
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    
    creds = None
    token_file = "token.json"
    
    # Load existing token
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)
    
    # If no valid token, get new one
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("✅ Token refreshed successfully!")
        else:
            print("🌐 Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            creds = flow.run_local_server(port=0)
            print("✅ Authentication completed!")
        
        # Save credentials for next run
        with open(token_file, "w") as token:
            pickle.dump(creds, token)
        print(f"✅ Token saved to {token_file}")
        
        return creds
    else:
        print("✅ Already authenticated!")
        return creds

if __name__ == "__main__":
    try:
        creds = manual_auth()
        print(f"🎉 Authentication successful!")
        print(f"📧 Email: {creds.client_id if hasattr(creds, 'client_id') else 'N/A'}")
        print(f"🔑 Token expires: {creds.expiry if hasattr(creds, 'expiry') else 'N/A'}")
        print()
        print("🚀 Now you can upload videos! Run:")
        print("   python youtube_upload_test.py")
    except Exception as e:
        print(f"❌ Error: {e}")