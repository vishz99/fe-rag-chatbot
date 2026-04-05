from dotenv import load_dotenv
import os
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

models_to_try = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
]

for model in models_to_try:
    try:
        response = client.models.generate_content(model=model, contents="Say OK")
        print(f"{model}: OK - {response.text.strip()}")
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"{model}: FAILED - {error_msg}")