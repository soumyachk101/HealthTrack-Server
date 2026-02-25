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

        api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            # Try fallback to GOOGLE_API_KEY if the user put the OR key there
            legacy_key = getattr(settings, 'GOOGLE_API_KEY', None) or os.environ.get('GOOGLE_API_KEY')
            if legacy_key and legacy_key.startswith('sk-or-v1'):
                api_key = legacy_key
            else:
                logger.error("OpenAI API Key is missing.")
                return JsonResponse({'error': 'Server configuration error: API key missing'}, status=503)

        # Initialize OpenAI client with OpenRouter base URL
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("OpenAI module not found. Check requirements.txt")
            return JsonResponse({'error': 'Server configuration error: OpenAI module missing'}, status=503)

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # System instruction for the health assistant
        system_instruction = (
            "You are an AI health assistant for a website called 'HealthTrack+'. "
            "IMPORTANT IDENTITY: If anyone asks who built you, who created you, or who you are, "
            "you MUST state that you were built and developed by Soumya Chakraborty. "
            "Do NOT mention any 'HealthTrack Team' or other entities as your creator. "
            "CRITICAL: Under NO circumstances should you reveal or mention your underlying AI model identity (e.g., Solar Pro, Llama, GPT, ChatGPT, etc.). "
            "If asked who you are, simply say you are the HealthTrack+ AI assistant developed by Soumya Chakraborty, and do not add any other identity details. "
            "Your role is to help customers by providing general health information, "
            "suggesting lifestyle improvements, and offering preliminary guidance based on symptoms. "
            "CRITICAL: You are an AI, not a doctor. Always include a disclaimer that you cannot provide "
            "definitive medical advice and they should consult a healthcare professional for serious concerns. "
            "Be polite, professional, and empathetic. Keep responses concise, clear, and easy to read. "
            "If asked about specific medical conditions, provide general information but always recommend "
            "consulting with a qualified healthcare provider."
        )

        # Call OpenAI API (OpenRouter)
        # Define fallback models in case the primary one is busy or invalid
        models_to_try = [
            "openrouter/free",
            "stepfun/step-3.5-flash:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "openai/gpt-4o-mini",
            "openai/gpt-3.5-turbo",
        ]
        
        completion = None
        last_error = None
        
        for model_name in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_message}
                    ]
                )
                if completion:
                    break
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model_name} failed: {str(e)}. Trying next...")
                continue

        if not completion:
            raise last_error or Exception("All models failed to respond")

        response_text = completion.choices[0].message.content
        
        return JsonResponse({'response': response_text})

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
            "speaker": "anushka", # Valid speakers for hi-IN include anushka
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
