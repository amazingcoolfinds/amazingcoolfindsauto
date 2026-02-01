import subprocess
import json

def check_video(path):
    print(f"🔍 Checking: {path}")
    cmd = f'ffprobe -v error -show_entries stream=codec_type,codec_name,bit_rate -of json {path}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        video_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
        audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)
        
        if video_stream:
            print(f"✅ Video: {video_stream.get('codec_name')} {video_stream.get('bit_rate')} bps")
        else:
            print("❌ No Video Stream found!")
            
        if audio_stream:
            print(f"✅ Audio: {audio_stream.get('codec_name')} {audio_stream.get('bit_rate')} bps")
        else:
            print("❌ No Audio Stream found!")
    else:
        print(f"❌ Error running ffprobe: {result.stderr}")

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "output_videos/video_B0866S3D82.mp4"
    check_video(path)
