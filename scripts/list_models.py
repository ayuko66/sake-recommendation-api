
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found")
else:
    genai.configure(api_key=api_key)
    print("Listing models...")
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(m.name)
