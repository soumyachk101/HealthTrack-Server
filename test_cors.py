import requests
import json

API_URL = "https://health-track-server-eight.vercel.app/chatbot/api/"

headers = {
    "Content-Type": "application/json",
    "Origin": "https://www.healthtrack.store",
}

payload = {"message": "Hello"}

# Test with OPTIONS (preflight)
print("=== PREFLIGHT (OPTIONS) ===")
try:
    r = requests.options(API_URL, headers={
        "Origin": "https://www.healthtrack.store",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    })
    print(f"Status: {r.status_code}")
    for k, v in r.headers.items():
        if 'access-control' in k.lower() or 'cors' in k.lower():
            print(f"  {k}: {v}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== POST REQUEST ===")
try:
    r = requests.post(API_URL, json=payload, headers=headers)
    print(f"Status: {r.status_code}")
    for k, v in r.headers.items():
        if 'access-control' in k.lower():
            print(f"  {k}: {v}")
    print(f"Body: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
