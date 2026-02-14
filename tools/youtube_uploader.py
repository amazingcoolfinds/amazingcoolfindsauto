#!/usr/bin/env python3
import os
import pickle
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

log = logging.getLogger("YouTubeUploader")

class YouTubeUploader:
    def __init__(self, client_secrets_file=None):
        if client_secrets_file is None:
            client_secrets_file = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "client_secret.json")
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.client_secrets_file = client_secrets_file
        self.credentials = self._get_credentials()
        self.youtube = build("youtube", "v3", credentials=self.credentials)

    def _get_credentials(self):
        creds = None
        if os.path.exists("token.json"):
            with open("token.json", "rb") as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes
                )
                # This will open a browser window for first-time auth
                creds = flow.run_local_server(port=0)
            
            with open("token.json", "wb") as token:
                pickle.dump(creds, token)
        
        return creds

    def upload_short(self, video_path, title, description, tags):
        """
        Uploads a video to YouTube with #Shorts in the title for automatic conversion.
        """
        if not os.path.exists(video_path):
            log.error(f"Video file not found: {video_path}")
            return None

        # Force #Shorts in title if not present
        if "#Shorts" not in title:
            title = f"{title} #Shorts"

        body = {
            "snippet": {
                "title": title[:100], # YouTube limit
                "description": description,
                "tags": tags,
                "categoryId": "22" # People & Blogs
            },
            "status": {
                "privacyStatus": "public", # Change to "unlisted" for testing
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(
            video_path, 
            mimetype="video/mp4", 
            resumable=True
        )

        log.info(f"🚀 Uploading to YouTube: {title}")
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.info(f"   Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        video_url = f"https://youtu.be/{video_id}"
        log.info(f"✅ Video uploaded successfully! ID: {video_id} - URL: {video_url}")
        return video_url

if __name__ == "__main__":
    # Test execution
    logging.basicConfig(level=logging.INFO)
    uploader = YouTubeUploader()
    # uploader.upload_short("output_videos/sample.mp4", "Test Short", "Testing automation", ["test", "shorts"])
