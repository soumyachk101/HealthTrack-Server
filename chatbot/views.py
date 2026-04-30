from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
# from openai import OpenAI # Moved inside view to prevent startup errors if missing
import json
import logging
import os
import requests

logger = logging.getLogger(__name__)

system_instruction = """
You are HealthTrack+ AI, a helpful and professional medical assistant. 
Your goal is to help users understand their health data, provide general wellness advice, 
and assist with navigating the HealthTrack+ platform.
Always include a disclaimer that you are an AI and not a substitute for professional medical advice.
"""

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def chat_api(request):
    # CORS preflight support (browser sends OPTIONS for application/json)
    if request.method == "OPTIONS":
        return JsonResponse({}, status=200)

    api_key = None
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')

        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        # Check for Groq API Key first if preferred
        groq_key = getattr(settings, 'GROQ_API_KEY', None) or os.environ.get('GROQ_API_KEY')
        print(f"DEBUG: Chatbot attempt - Groq Key Present: {bool(groq_key and groq_key != 'your_groq_api_key_here')}")
        
        if groq_key and groq_key != 'your_groq_api_key_here':
            try:
                print("DEBUG: Calling Groq API...")
                response = requests.post(
                    url="https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    data=json.dumps({
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_message}
                        ]
                    })
                )
                print(f"DEBUG: Groq Response Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    completion_text = data['choices'][0]['message']['content']
                    return JsonResponse({'response': completion_text})
                else:
                    print(f"DEBUG: Groq Error Body: {response.text}")
                    logger.warning(f"Groq API error: {response.text}. Falling back to OpenRouter.")
            except Exception as e:
                print(f"DEBUG: Groq Exception: {str(e)}")
                logger.warning(f"Groq connection failed: {str(e)}. Falling back to OpenRouter.")

        # Fallback to OpenRouter
        api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
        print(f"DEBUG: Fallback to OpenRouter - Key Present: {bool(api_key)}")
        
        if not api_key:
            # Try fallback to GOOGLE_API_KEY if the user put the OR key there
            legacy_key = getattr(settings, 'GOOGLE_API_KEY', None) or os.environ.get('GOOGLE_API_KEY')
            if legacy_key and legacy_key.startswith('sk-or-v1'):
                api_key = legacy_key
            else:
                logger.error("OpenAI API Key is missing.")
                return JsonResponse({'error': 'Server configuration error: API key missing'}, status=503)

        try:
            print("DEBUG: Calling OpenRouter API...")
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_message}
                    ]
                })
            )
            print(f"DEBUG: OpenRouter Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"DEBUG: OpenRouter Error Body: {response.text}")
                raise Exception(f"OpenRouter API error: {response.text}")
                
            data = response.json()
            completion_text = data['choices'][0]['message']['content']
            return JsonResponse({'response': completion_text})
            
        except Exception as e:
            print(f"DEBUG: Chatbot Final Exception: {str(e)}")
            logger.error(f"Chatbot API error: {str(e)}")
            return JsonResponse({'error': f'Chat service failed: {str(e)}'}, status=500)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Error in chat_api: {str(e)}", exc_info=True)
        # Don't leak internal errors in production responses.
        if getattr(settings, "DEBUG", False):
            error_message = f"DEBUG ERROR: {str(e)} | KeyPresent: {bool(api_key)}"
            return JsonResponse({'error': error_message}, status=500)
        return JsonResponse({'error': 'Chat service error. Please try again later.'}, status=500)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def tts_api(request):
    """
    Endpoint to convert text to speech using Sarvam API.
    Expects JSON: { "text": "Hello world" }
    """
    if request.method == "OPTIONS":
        return JsonResponse({}, status=200)

    api_key = getattr(settings, 'SARVAM_API_KEY', None) or os.environ.get('SARVAM_API_KEY')
    if not api_key or api_key == 'your_sarvam_api_key_here':
        logger.error("Sarvam API Key is missing or invalid.")
        return JsonResponse({'error': 'TTS configuration error: API key missing'}, status=503)

    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()

        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        # Truncate text if necessary to fit within limits (500 chars per Sarvam API docs request)
        if len(text) > 450:
             text = text[:450] + "..."

        url = "https://api.sarvam.ai/text-to-speech"
        
        # Determine language (e.g., if it has Hindi characters, use hi-IN, else fallback to en-IN)
        # Using hi-IN for Hindi setup or en-IN for English with Indian accent. Let's use en-IN by default.
        payload = {
            "inputs": [text],
            "target_language_code": "hi-IN",
            "speaker": "priya", # Valid speakers for hi-IN include anushka, priya
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": api_key
        }

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if "audios" in result and len(result["audios"]) > 0:
                audio_base64 = result["audios"][0]
                return JsonResponse({'audio': audio_base64})
            else:
                 logger.error(f"Sarvam API returned unexpected format: {result}")
                 return JsonResponse({'error': 'Invalid response from TTS service'}, status=500)
        else:
            logger.error(f"Sarvam API error: {response.status_code} - {response.text}")
            return JsonResponse({'error': f'TTS service error: {response.status_code}'}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Error in tts_api: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'TTS service encountered an error.'}, status=500)
