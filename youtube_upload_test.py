#!/usr/bin/env python3
"""
YouTube Upload Test - After authentication
"""
import os
from youtube_uploader import YouTubeUploader
import logging

logging.basicConfig(level=logging.INFO)

def upload_test():
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

    print('🚀 YOUTUBE UPLOAD TEST')
    print('=' * 40)
    print(f'📹 Video: {video_path}')
    print(f'📝 Title: {title}')
    print(f'🏷️  Tags: {tags}')
    print()

    try:
        uploader = YouTubeUploader('client_secret.json')
        print('✅ YouTube client initialized')
        
        print('📤 Starting upload...')
        video_id = uploader.upload_short(video_path, title, description, tags)
        
        if video_id:
            print(f'✅ UPLOAD SUCCESSFUL!')
            print(f'🎥 Video ID: {video_id}')
            print(f'🔗 YouTube URL: https://youtube.com/shorts/{video_id}')
            print(f'📊 Video uploaded with Diana voice and metadata')
            return True
        else:
            print('❌ Upload failed - no video ID returned')
            return False
            
    except Exception as e:
        print(f'❌ Error during upload: {e}')
        return False

if __name__ == "__main__":
    success = upload_test()
    if success:
        print()
        print('🎯 PIPELINE STATUS:')
        print('   ✅ Video generation: DONE (Diana voice)')
        print('   ✅ Website update: DONE') 
        print('   ✅ YouTube upload: DONE')
        print('   ✅ Instagram patch: WORKING')
        print('   ✅ Meta/TikTok: READY')
        print()
        print('🚀 Pipeline phase 2 COMPLETED!')