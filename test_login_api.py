import requests
import json

# Configuration
API_URL = "https://health-track-server-eight.vercel.app"
LOGIN_URL = f"{API_URL}/accounts/api/login/"
USERNAME = "testsprite"
PASSWORD = "testpassword123"

def test_login():
    print(f"Testing login at {LOGIN_URL}...")
    
    headers = {
        "Content-Type": "application/json",
        # Simulate a request from the frontend domain to check CORS (though requests library doesn't enforce CORS, the server might check Origin)
        "Origin": "https://www.healthtrack.store" 
    }
    
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(LOGIN_URL, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        
        try:
            data = response.json()
            print(f"Response Body: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Body (Raw): {response.text}")
            
        if response.status_code == 200:
            print("\n✅ LOGIN SUCCESSFUL")
            if 'token' in data or 'access' in data or 'key' in data:
                 print("✅ Token received")
            else:
                 print("⚠️ No token found in response (check auth implementation)")
        else:
            print("\n❌ LOGIN FAILED")

    except Exception as e:
        print(f"\n❌ REQUEST FAILED: {str(e)}")

if __name__ == "__main__":
    test_login()
