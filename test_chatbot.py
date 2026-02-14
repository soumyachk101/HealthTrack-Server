import requests
import json

url = 'http://localhost:8000/chatbot/api/'
headers = {'Content-Type': 'application/json'}
data = {'message': 'Hello, are you working?'}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
