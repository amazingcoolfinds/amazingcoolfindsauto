import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# The model name found in list_models
model_name = 'gemini-2.5-flash-preview-tts'

print(f"Trying to use {model_name} for TTS...")
try:
    model = genai.GenerativeModel(model_name)
    # The TTS model usually takes text and outputs audio modality
    response = model.generate_content(
        "Welcome to the luxury of tomorrow. Skincare redefined.",
        generation_config={"response_modalities": ["AUDIO"]}
    )
    
    found = False
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            print(f"✅ Audio received! {len(part.inline_data.data)} bytes")
            with open("gemini_voice_test.wav", "wb") as f:
                f.write(part.inline_data.data)
            found = True
            break
    if not found:
        print("❌ No audio part found.")
except Exception as e:
    print(f"❌ Error using {model_name}: {e}")
