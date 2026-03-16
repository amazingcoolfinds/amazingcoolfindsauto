import os
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("UploadPostUploader")

class UploadPostUploader:
    def __init__(self, api_key, user="amazingcool"):
        self.api_key = api_key
        self.user = user
        self.base_url = "https://api.upload-post.com"
    
    def upload_video(self, video_path, title, description="", platforms=None, affiliate_link=None):
        """
        Upload video to multiple platforms
        
        Args:
            video_path: Path to video file or URL
            title: Video title
            description: Video description
            platforms: List of platforms ['tiktok', 'instagram', 'facebook', 'youtube', 'pinterest']
            affiliate_link: Link to include in post
        
        Returns:
            dict with results per platform
        """
        if platforms is None:
            platforms = ["youtube", "instagram", "facebook", "tiktok"]
        
        headers = {
            "Authorization": f"Apikey {self.api_key}"
        }
        
        first_comment = f"🔥 Check it out: {affiliate_link}" if affiliate_link else None
        
        data = {
            "user": self.user,
            "platform[]": platforms,
            "title": title[:2200],
            "description": description[:5000] if description else "",
            "first_comment": first_comment,
            "privacy_status": "public"
        }
        
        if video_path.startswith("http"):
            data["video"] = video_path
        else:
            try:
                with open(video_path, "rb") as f:
                    files = {"video": f}
                    response = requests.post(
                        f"{self.base_url}/api/upload",
                        headers=headers,
                        data=data,
                        files=files,
                        timeout=300
                    )
            except Exception as e:
                log.error(f"❌ Failed to read video file: {e}")
                return None
        
        try:
            result = response.json()
            
            if result.get("success"):
                log.info(f"✅ Upload successful to {len(result.get('results', {}))} platforms")
                return result
            else:
                log.error(f"❌ Upload failed: {result.get('message')}")
                return result
                
        except Exception as e:
            log.error(f"❌ Upload error: {e}")
            return None
    
    def upload_from_url(self, video_url, title, description="", platforms=None, affiliate_link=None):
        """Upload video from URL"""
        if platforms is None:
            platforms = ["youtube", "instagram", "facebook", "tiktok"]
        
        headers = {
            "Authorization": f"Apikey {self.api_key}"
        }
        
        first_comment = f"🔥 Check it out: {affiliate_link}" if affiliate_link else None
        
        data = {
            "user": self.user,
            "platform[]": platforms,
            "title": title[:2200],
            "description": description[:5000] if description else "",
            "first_comment": first_comment,
            "video": video_url,
            "privacy_status": "public"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/upload",
                headers=headers,
                data=data,
                timeout=300
            )
            
            result = response.json()
            
            if result.get("success"):
                log.info(f"✅ Upload successful to {len(result.get('results', {}))} platforms")
                return result
            else:
                log.error(f"❌ Upload failed: {result.get('message')}")
                return result
                
        except Exception as e:
            log.error(f"❌ Upload error: {e}")
            return None
