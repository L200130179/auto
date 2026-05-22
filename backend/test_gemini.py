import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")
print("API KEY length:", len(api_key) if api_key else "None")
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    response = model.generate_content("Hello! Give me a JSON with { 'test': 'ok' }")
    print("Success:", response.text)
except Exception as e:
    print("Error:", repr(e))
