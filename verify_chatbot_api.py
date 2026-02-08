import requests
import json

def verify_chatbot():
    url = "http://localhost:8000/chatbot/api/"
    payload = {"message": "Hello, can you help me with a health tip?"}
    headers = {"Content-Type": "application/json"}
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data:
                print("SUCCESS: Chatbot responded correctly.")
                print(f"Chatbot Response: {data['response'][:100]}...")
                return True
            else:
                print("FAILURE: 'response' field missing in JSON.")
        else:
            print(f"FAILURE: Received error status {response.status_code}")
            print(f"Error Message: {response.text}")
            
    except Exception as e:
        print(f"ERROR: Could not connect to chatbot API. {e}")
        
    return False

if __name__ == "__main__":
    verify_chatbot()
