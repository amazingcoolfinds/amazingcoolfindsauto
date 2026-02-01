import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Using gemini-2.0-flash which supports multimodal output
model = genai.GenerativeModel('gemini-2.0-flash')

prompt = "Read this skyscraper description with a luxury and energetic voice: 'This is the most incredible view in the world.'"

print("Trying to generate audio with Gemini 2.0 Flash (response_modalities)...")
try:
    # Gemini 2.0 Flash supports 'AUDIO' modality
    response = model.generate_content(
        prompt,
        generation_config={
            "response_modalities": ["AUDIO"],
        }
    )
    
    audio_found = False
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            print(f"✅ Audio data received! Size: {len(part.inline_data.data)} bytes")
            # Usually it's PCM or similar, we might need to verify the format
            with open("test_gemini_voice.wav", "wb") as f:
                f.write(part.inline_data.data)
            audio_found = True
            break
            
    if not audio_found:
        print("❌ No audio data in response parts.")
        print(f"Response content: {response.candidates[0].content}")
        
except Exception as e:
    print(f"❌ Gemini Audio Error: {e}")
