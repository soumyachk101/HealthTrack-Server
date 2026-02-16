from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.conf import settings
# from openai import OpenAI # Moved inside view to prevent startup errors if missing
import json
import logging
import os

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
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
            "google/gemini-2.0-flash-lite-preview-02-05:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "mistralai/mistral-small-24b-instruct-2501:free",
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
        # TEMPORARY DEBUGGING: Always return the real error
        error_message = f'DEBUG ERROR: {str(e)} | Key: {bool(api_key)}' 
        return JsonResponse({'error': error_message}, status=500)
