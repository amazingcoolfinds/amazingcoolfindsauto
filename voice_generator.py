#!/usr/bin/env python3
import os
import google.generativeai as genai
import logging
from pathlib import Path

log = logging.getLogger("VoiceGenerator")

class VoiceGenerator:
    """
    Generates high-quality human-like voiceovers using Gemini TTS models.
    Uses the user's existing GEMINI_API_KEY.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.output_dir = Path("temp")
        self.output_dir.mkdir(exist_ok=True)
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use the validated TTS preview model
            self.model = genai.GenerativeModel('gemini-2.5-flash-preview-tts')
        
    def generate(self, text: str, asin: str) -> str:
        """
        Converts text to speech using Gemini with retry logic.
        """
        if not self.api_key:
            log.error("GEMINI_API_KEY missing for VoiceGenerator.")
            return None
            
        output_path = self.output_dir / f"voice_{asin}.wav"
        
        import time
        max_retries = 3
        base_delay = 35 # Gemini free tier delay is often ~30s
        
        for attempt in range(max_retries):
            try:
                log.info(f"Generating Gemini voiceover for {asin} (Attempt {attempt+1}/{max_retries})...")
                
                response = self.model.generate_content(
                    text,
                    generation_config={
                        "response_modalities": ["AUDIO"]
                    }
                )
                
                audio_data = None
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        audio_data = part.inline_data.data
                        break
                
                if audio_data:
                    with open(output_path, "wb") as f:
                        f.write(audio_data)
                    log.info(f"✅ Gemini Voiceover created: {output_path}")
                    return str(output_path)
                else:
                    log.error("No audio data returned from Gemini TTS.")
                    
            except Exception as e:
                error_msg = str(e)
                log.warning(f"Voice generation attempt {attempt+1} failed: {error_msg}")
                
                if "429" in error_msg or "quota" in error_msg.lower():
                    delay = base_delay * (attempt + 1)
                    log.info(f"⏱️ Rate limit hit. Waiting {delay}s before retry...")
                    time.sleep(delay)
                else:
                    # Non-quota error, still retry or break
                    time.sleep(5)
                    
        log.error(f"❌ Failed to generate voiceover after {max_retries} attempts.")
        return None
