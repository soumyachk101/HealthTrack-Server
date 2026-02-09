from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from openai import OpenAI
import json
import logging
import os

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def chat_api(request):
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            if not user_message:
                response = JsonResponse({'error': 'No message provided'}, status=400)
                response['Access-Control-Allow-Origin'] = '*'
                return response

            api_key = settings.OPENAI_API_KEY or os.environ.get('OPENAI_API_KEY')
            
            if not api_key:
                # Try fallback to GOOGLE_API_KEY if the user put the OR key there
                legacy_key = settings.GOOGLE_API_KEY or os.environ.get('GOOGLE_API_KEY')
                if legacy_key and legacy_key.startswith('sk-or-v1'):
                    api_key = legacy_key
                else:
                    response = JsonResponse({'error': 'Server configuration error: API key missing'}, status=503)
                    response['Access-Control-Allow-Origin'] = '*'
                    return response

            # Initialize OpenAI client with OpenRouter base URL
            client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "HealthTrack+"
                }
            )

            # System instruction for the health assistant
            system_instruction = (
                "You are an AI health assistant for a website called 'HealthTrack+'. "
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
                "meta-llama/llama-3.2-3b-instruct:free",
                "google/gemma-3-27b-it:free",
                "mistralai/mistral-small-3.1-24b-instruct:free",
                "openai/gpt-oss-120b:free"
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
            
            response = JsonResponse({'response': response_text})
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            response = JsonResponse({'error': 'Invalid JSON format'}, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        except Exception as e:
            logger.error(f"Error in chat_api: {str(e)}", exc_info=True)
            error_message = 'An error occurred while processing your request. Please try again.'
            if settings.DEBUG:
                error_message = f'An error occurred: {str(e)}'
            response = JsonResponse({'error': error_message}, status=500)
            response['Access-Control-Allow-Origin'] = '*'
            return response

    response = JsonResponse({'error': 'Invalid request method'}, status=405)
    response['Access-Control-Allow-Origin'] = '*'
    return response
