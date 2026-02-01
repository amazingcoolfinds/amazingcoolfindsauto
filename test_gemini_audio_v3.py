import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model_name = 'models/gemini-1.5-flash' # Testing with 1.5 flash first

print(f"Trying to use {model_name} for TTS...")
try:
    # Some versions of the API/SDK allow audio generation by asking for it 
    # and setting the modality if the model supports it.
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        "Generate a high quality audio file of a person saying: 'Welcome to the luxury of tomorrow. Skincare redefined.'",
        generation_config={"response_modalities": ["AUDIO"]}
    )
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
