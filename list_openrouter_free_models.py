import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    # Try fallback
    legacy_key = os.environ.get('GOOGLE_API_KEY')
    if legacy_key and legacy_key.startswith('sk-or-v1'):
        api_key = legacy_key

if not api_key:
    print("API Key missing")
    exit(1)

print("Fetching models from OpenRouter...")
response = requests.get("https://openrouter.ai/api/v1/models", headers={
    "Authorization": f"Bearer {api_key}"
})

if response.status_code == 200:
    models = response.json().get('data', [])
    free_models = [m['id'] for m in models if 'free' in m['id']]
    print("Free models found:")
    for m in free_models:
        print(f"- {m}")
else:
    print(f"Error fetching models: {response.status_code}")
    print(response.text)
