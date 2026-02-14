import json
import jwt
import datetime
from functools import wraps
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

def jwt_required(view_func):
    """Decorator that authenticates requests using JWT Bearer token."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization header missing or invalid'}, status=401)

        token = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        User = get_user_model()
        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=401)

        request.user = user
        return view_func(request, *args, **kwargs)
    return wrapper

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
            role = data.get('role', 'patient')  # Get role, default to patient
            
            User = get_user_model()
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Username already exists'}, status=400)
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Email already registered'}, status=400)
            
            # Determine user_type based on role
            if role == 'doctor':
                user_type = 'provider'
                provider_type = 'doctor'
                is_approved = False  # Doctors need approval
            elif role == 'provider': # 'service_provider' or just 'provider'
                user_type = 'provider'
                provider_type = data.get('provider_type', 'pharmacy')
                is_approved = False
            else:
                user_type = 'patient'
                provider_type = None
                is_approved = True

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                is_approved=is_approved
            )
            
            # Create ServiceProvider profile if needed
            if user_type == 'provider':
                ServiceProvider.objects.create(
                    user=user,
                    provider_type=provider_type,
                    business_name=data.get('business_name', f"{first_name} {last_name}")
                )
            
            # Auto login to get token immediately
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            
            token = generate_token(user)
             
            ActivityLog.objects.create(
                user=user,
                action='register_api',
                details=f"User registered via API as {role}"
            )
            
            return JsonResponse({
                'success': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': role
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
