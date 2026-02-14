#!/usr/bin/env python3
import os
import logging
import subprocess
import requests
from pathlib import Path

log = logging.getLogger("VideoGenerator")

class VideoGenerator:
    """
    Generates vertical short-form videos from product images and script.
    Optimized for high-quality retention and social media aesthetic.
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
        image_urls = product.get('images', [product.get('image_url')])
        
        try:
            # 1. Download up to 7 images (filter successful downloads)
            local_images = []
            # Ensure image_urls is a list
            if not isinstance(image_urls, list):
                if image_urls: image_urls = [image_urls]
                else: image_urls = []
                
            for i, url in enumerate(image_urls[:7]):
                path = self.temp_dir / f"img_{asin}_{i}.jpg"
                if self._download_image(url, path):
                    local_images.append(path)
            
            # Ensure we have at least 1 image
            if not local_images:
                log.error(f"No images downloaded for {asin}")
                if output_path.exists(): output_path.unlink()
                return None
            
            log.info(f"✓ Downloaded {len(local_images)} images for carousel")
            
            # --- DYNAMIC DURATION LOGIC ---
            # Default to 18s if no voice, but if voice exists, measure it
            total_vid_dur = 18.0 # Default
            if voice_path and os.path.exists(voice_path):
                try:
                    # Use ffprobe to get accurate duration for MP3 files
                    probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{voice_path}"'
                    result = subprocess.run(probe_cmd, shell=True, capture_output=True, text=True)
                    voice_dur = float(result.stdout.strip())
                    total_vid_dur = voice_dur + 1.5  # Add buffer for smooth ending
                    log.info(f"🎤 Voice duration: {voice_dur:.2f}s. Setting video to {total_vid_dur:.2f}s")
                except Exception as e:
                    log.warning(f"Could not calculate voice duration: {e}. Using default 18s")
            
            num_images = len(local_images)
            fade_dur = 0.5
            # Formula: total_vid_dur = (num_images * segment_dur) - ((num_images - 1) * fade_dur)
            # -> segment_dur = (total_vid_dur + (num_images - 1) * fade_dur) / num_images
            segment_dur = (total_vid_dur + (num_images - 1) * fade_dur) / num_images
            
            # 2. Build Filter Complex (Using list to avoid syntax errors)
            filter_chains = []
            
            # 2.1 Input Scaling
            for i in range(num_images):
                filter_chains.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}_base]")

            # 2.2 Transitions or Single Image Base
            if num_images == 1:
                filter_chains.append(f"[v0_base]format=yuv420p[vout]")
            else:
                last_label = "[v0_base]"
                for i in range(1, num_images):
                    offset = i * (segment_dur - fade_dur)
                    next_label = f"[v_fade{i}]"
                    if i == num_images - 1:
                        next_label = "[vout_raw]"
                    
                    filter_chains.append(f"{last_label}[v{i}_base]xfade=transition=fade:duration={fade_dur}:offset={offset}{next_label}")
                    last_label = next_label

                # Final visual formatting
                filter_chains.append(f"[vout_raw]format=yuv420p[vout]")
            
            # 2.3 Audio Mixing
            voice_idx = num_images
            bg_music = self.assets_dir / "background_music.mp3"
            
            if voice_path and os.path.exists(voice_path):
                audio_inputs = f"-i {voice_path} "
                if bg_music.exists():
                    audio_inputs += f"-stream_loop -1 -i {bg_music} "
                    bg_idx = voice_idx + 1
                    filter_chains.append(f"[{voice_idx}:a]volume=2.0[v_a]")
                    filter_chains.append(f"[{bg_idx}:a]volume=0.05,atrim=0:{total_vid_dur}[m_a]")
                    filter_chains.append(f"[v_a][m_a]amix=inputs=2:duration=first[aout]")
                else:
                    filter_chains.append(f"[{voice_idx}:a]volume=2.0[aout]")
            else:
                log.error("❌ Audio mixing failed: Voice path missing or invalid.")
                if output_path.exists(): output_path.unlink()
                return None

            # Join all filters safely
            full_filter = "; ".join(filter_chains)

            cmd = f'ffmpeg -y '
            for img in local_images:
                cmd += f'-loop 1 -t {segment_dur} -i {img} '
            
            # Standardize output format for maximum compatibility (QuickTime/iPhone)
            # -ac 2 (Stereo)
            # -ar 44100 (44.1kHz)
            # -pix_fmt yuv420p (Required for broad H.264 support)
            
            cmd += (
                f'{audio_inputs} -filter_complex "{full_filter}" '
                f'-map "[vout]" -map "[aout]" '
                f'-c:v libx264 -profile:v high -level:v 4.0 -pix_fmt yuv420p -crf 23 -r 30 '
                f'-color_range 1 -colorspace bt709 -color_trc bt709 -color_primaries bt709 '
                f'-c:a aac -b:a 192k -ac 2 -ar 44100 -shortest -t {total_vid_dur} -movflags +faststart {output_path}'
            )
            
            log.info(f"Generating video for {asin}...")
            # Run FFmpeg
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                log.error(f"FFmpeg failed: {result.stderr}")
                if output_path.exists(): output_path.unlink() # Delete broken file
                return None
                
            if output_path.exists() and output_path.stat().st_size > 0:
                log.info(f"✅ Refined Video created: {output_path} ({output_path.stat().st_size/1024/1024:.2f} MB)")
                return str(output_path)
            else:
                log.error("Video file created but is empty")
                if output_path.exists(): output_path.unlink()
                return None
            
        except Exception as e:
            log.error(f"Failed to generate carousel video: {e}")
            if output_path.exists(): output_path.unlink() # Cleanup
            return None

    def _download_image(self, url: str, path: Path) -> bool:
        """Download image and return True if successful"""
        try:
            if not url: return False
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(path, 'wb') as f:
                f.write(response.content)
            return path.exists() and path.stat().st_size > 0
        except Exception as e:
            log.warning(f"Could not download image: {url} - {e}")
            return False
