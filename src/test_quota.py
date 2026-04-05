from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

# Test OpenRouter with Qwen 3.6 Plus
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

try:
    response = client.chat.completions.create(
        model="qwen/qwen3.6-plus:free",
        messages=[{"role": "user", "content": "Say OK"}]
    )
    print(f"Qwen 3.6 Plus: OK - {response.choices[0].message.content.strip()}")
except Exception as e:
    print(f"Qwen 3.6 Plus: FAILED - {str(e)[:200]}")