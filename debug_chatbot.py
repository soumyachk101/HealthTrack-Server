import requests
import json

url = 'http://localhost:8000/chatbot/api/'
headers = {'Content-Type': 'application/json'}
data = {'message': 'Hello, are you working?'}

try:
    response = requests.post(url, headers=headers, json=data)
    with open('debug_output.txt', 'w') as f:
        f.write(f"Status Code: {response.status_code}\n")
        f.write(f"Response: {response.text}\n")
    print("Debug output written to debug_output.txt")
except Exception as e:
    print(f"Error: {e}")
