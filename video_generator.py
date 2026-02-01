#!/usr/bin/env python3
import os
import subprocess
import requests
import logging
from pathlib import Path
from typing import List

log = logging.getLogger("VideoGenerator")

class VideoGenerator:
    """
    Generates viral vertical videos (9:16) with a multi-image carousel
    and synchronized voiceover.
    """
    
    def __init__(self):
        self.output_dir = Path("output_videos")
        self.temp_dir = Path("temp")
        self.assets_dir = Path("assets")
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)

    def generate(self, product: dict, script: dict, voice_path: str = None) -> str:
        """
        Creates a vertical carousel video.
        """
        asin = product.get('asin', 'unknown')
        output_path = self.output_dir / f"video_{asin}.mp4"
        image_urls = product.get('images', [product['image_url']])
        
        try:
            # 1. Download up to 5 images
            local_images = []
            for i, url in enumerate(image_urls[:5]):
                path = self.temp_dir / f"img_{asin}_{i}.jpg"
                self._download_image(url, path)
                local_images.append(path)
            
            # 2. Build Filter Complex with "Premium Aesthetic" & XFADE Transitions
            import re
            def clean(t): 
                t = t.encode('ascii', 'ignore').decode('ascii')
                return t.replace(":", "\\:").replace("'", "").replace(",", "").replace('"', "").replace(";", "").strip()
            
            # --- DYNAMIC DURATION LOGIC ---
            # Default to 18s if no voice, but if voice exists, measure it
            total_vid_dur = 18.0 # Default
            if voice_path and os.path.exists(voice_path):
                try:
                    # Gemini returns raw PCM 24kHz 16-bit Mono
                    # Duration = Bytes / (SampleRate * BytesPerSample * Channels)
                    # 24000 * 2 * 1 = 48000 bytes per second
                    file_size = os.path.getsize(voice_path)
                    voice_dur = file_size / 48000.0
                    total_vid_dur = voice_dur + 1.2 # Add buffer for smooth ending
                    log.info(f"🎤 Voice duration calculated: {voice_dur:.2f}s (Size: {file_size}). Setting video to {total_vid_dur:.2f}s")
                except Exception as e:
                    log.warning(f"Could not calculate voice duration: {e}. Using default 18s")
            
            # Calculate segment duration to fit the total time
            # Formula: total = N * (seg_dur - fade) + fade
            # seg_dur = (total - fade) / N + fade
            fade_dur = 0.5
            num_images = len(local_images)
            segment_dur = ((total_vid_dur - fade_dur) / num_images) + fade_dur
            log.info(f"⏱️ Calculated segment duration: {segment_dur:.2f}s per image")

            # Prepare each segment with blur background and sharp foreground
            filters = ""
            for i in range(len(local_images)):
                filters += (
                    f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[v{i}_bg]; "
                    f"[{i}:v]scale=900:-1[v{i}_fg]; "
                    f"[v{i}_bg][v{i}_fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v{i}_base]; "
                )
            
            # 3. Chain XFADE transitions
            last_label = "[v0_base]"
            for i in range(1, num_images):
                offset = i * (segment_dur - fade_dur)
                next_label = f"[v_fade{i}]"
                if i == num_images - 1:
                    next_label = "[vout_raw]"
                
                filters += f"{last_label}[v{i}_base]xfade=transition=fade:duration={fade_dur}:offset={offset}{next_label}; "
                last_label = next_label

            # Final visual processing (force format for Mac)
            filters += f"[vout_raw]format=yuv420p[vout]"
            
            # Robust Audio Mixing (Voice MANDATORY)
            voice_idx = num_images
            bg_music = self.assets_dir / "background_music.mp3"
            
            if voice_path and os.path.exists(voice_path):
                audio_inputs = f"-f s16le -ar 24000 -ac 1 -i {voice_path} "
                if bg_music.exists():
                    audio_inputs += f"-stream_loop -1 -i {bg_music} "
                    bg_idx = voice_idx + 1
                    audio_filter = f"[{voice_idx}:a]volume=2.0[v_a]; [{bg_idx}:a]volume=0.05,atrim=0:{total_vid_dur}[m_a]; [v_a][m_a]amix=inputs=2:duration=first[aout]"
                else:
                    audio_filter = f"[{voice_idx}:a]volume=2.0[aout]"
            else:
                log.error("❌ Audio mixing failed: Voice path missing or invalid.")
                raise RuntimeError("Voice file missing for video generation.")

            cmd = f'ffmpeg -y '
            for img in local_images:
                cmd += f'-loop 1 -t {segment_dur} -i {img} '
            
            cmd += (
                f'{audio_inputs} -filter_complex "{filters}; {audio_filter}" '
                f'-map "[vout]" -map "[aout]" '
                f'-c:v libx264 -profile:v baseline -level:v 3.1 -pix_fmt yuv420p -crf 18 -r 30 '
                f'-color_range 1 -colorspace bt709 -color_trc bt709 -color_primaries bt709 '
                f'-c:a aac -b:a 128k -shortest -t {total_vid_dur} -movflags +faststart {output_path}'
            )
            
            log.info(f"Generating refined 3.1 video for {asin}...")
            result = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
            
            if result.returncode != 0:
                log.error(f"FFmpeg failed with exit code {result.returncode}")
                log.error(f"STDOUT: {result.stdout}")
                log.error(f"STDERR: {result.stderr}")
                raise RuntimeError(f"FFmpeg error: {result.stderr}")
                
            log.info(f"✅ Refined Video created: {output_path}")
            return str(output_path)
            
        except Exception as e:
            log.error(f"Failed to generate carousel video: {e}")
            return None

    def _download_image(self, url: str, path: Path):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(path, 'wb') as f:
                f.write(response.content)
        except:
            log.warning(f"Could not download image: {url}")
