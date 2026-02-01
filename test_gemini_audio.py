import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.0-flash')

prompt = "Read this skyscraper description with a luxury and energetic voice: 'This is the most incredible view in the world.'"

print("Trying to generate audio with Gemini 2.0 Flash...")
try:
    # Latest Gemini 2.0 supports speech output via response modality or specific config
    # In the current python SDK, it might be via 'response_mime_type': 'audio/wav' if supported
    # or just asking it to speak.
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "audio/wav"}
    )
    
    if hasattr(response, 'parts'):
        for part in response.parts:
            if hasattr(part, 'inline_data'):
                print(f"✅ Audio data received! Size: {len(part.inline_data.data)} bytes")
                with open("test_gemini_voice.wav", "wb") as f:
                    f.write(part.inline_data.data)
                break
    else:
        print("❌ No audio parts in response.")
except Exception as e:
    print(f"❌ Gemini Audio Error: {e}")
