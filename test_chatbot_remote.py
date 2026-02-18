import requests
import json
import os

# Use the key from the user's env provided earlier
OPENAI_API_KEY = "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" # Copied from user's env

API_URL = "https://health-track-server-eight.vercel.app/chatbot/api/"

def test_chatbot():
    print(f"Testing Chatbot API at {API_URL}...")
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "message": "Hello, are you working?"
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response Body (Raw): {response.text}")

    except Exception as e:
        print(f"Request Failed: {str(e)}")

if __name__ == "__main__":
    test_chatbot()
