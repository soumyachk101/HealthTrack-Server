import os
import django
from django.conf import settings
from django.http import HttpRequest
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthtracker.settings')
django.setup()

# Override settings for debugging
settings.DEBUG = True
# Use the user's key
os.environ['OPENAI_API_KEY'] = "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"

from chatbot.views import chat_api

def debug_view():
    print("Debugging chat_api view locally...")
    
    # Create a mock request
    request = HttpRequest()
    request.method = 'POST'
    request.headers = {'Content-Type': 'application/json'}
    request._body = json.dumps({
        "message": "Hello, this is a local debug test."
    }).encode('utf-8')
    
    try:
        response = chat_api(request)
        print(f"Status: {response.status_code}")
        print(f"Content: {response.content.decode('utf-8')}")
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_view()
