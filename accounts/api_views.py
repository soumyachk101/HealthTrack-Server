import json
import jwt
import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from .models import ServiceProvider
from core.models import ActivityLog

# User = get_user_model() # Moved inside functions to avoid AppRegistryNotReady

# Secret key for JWT encoding (use Django's SECRET_KEY)
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'

def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user:
                token = generate_token(user)
                login(request, user) # Optional for session, but good practice
                
                ActivityLog.objects.create(
                    user=user,
                    action='login_api',
                    details='User logged in via API'
                )
                
                return JsonResponse({
                    'success': True,
                    'token': token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': 'provider' if hasattr(user, 'serviceprovider') else 'patient' # Simplified role detection
                    }
                })
            else:
                return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@csrf_exempt
def register_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            
            User = get_user_model()
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Username already exists'}, status=400)
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Email already registered'}, status=400)
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Auto login to get token immediately? 
            # Or assume redirect to login? Let's return token for auto-login.
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            # login(request, user)
            
            token = generate_token(user)
             
            ActivityLog.objects.create(
                user=user,
                action='register_api',
                details='User registered via API'
            )
            
            return JsonResponse({
                'success': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
