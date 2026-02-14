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

import random
from core.utils import send_otp_email

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user:
                # Generate OTP
                otp = str(random.randint(100000, 999999))
                request.session['otp'] = otp
                request.session['otp_user_id'] = user.id
                request.session['otp_type'] = 'login'
                
                # Send OTP email
                send_otp_email(user.email, otp, user.first_name)
                
                return JsonResponse({
                    'success': True,
                    'otp_required': True,
                    'message': 'Verification code sent to your email'
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
            
            User = get_user_model()
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Username already exists'}, status=400)
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Email already registered'}, status=400)
            
            # Store registration data in session
            request.session['temp_reg_data'] = data
            
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['otp_type'] = 'register'
            
            # Send OTP email
            send_otp_email(email, otp, data.get('first_name'))
            
            return JsonResponse({
                'success': True,
                'otp_required': True,
                'message': 'Verification code sent to your email'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@csrf_exempt
def verify_otp_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            entered_otp = data.get('otp')
            generated_otp = request.session.get('otp')
            otp_type = request.session.get('otp_type')
            
            if not generated_otp:
                return JsonResponse({'success': False, 'error': 'Invalid or expired OTP'}, status=400)
            
            # Allow '999999' as a bypass in DEBUG mode for easier testing
            is_valid = (entered_otp == generated_otp) or (settings.DEBUG and entered_otp == '999999')
            
            if not is_valid:
                return JsonResponse({'success': False, 'error': 'Invalid or expired OTP'}, status=400)
            
            User = get_user_model()
            
            if otp_type == 'register':
                reg_data = request.session.get('temp_reg_data')
                role = reg_data.get('role', 'patient')
                
                # Create user
                user = User.objects.create_user(
                    username=reg_data.get('username'),
                    email=reg_data.get('email'),
                    password=reg_data.get('password'),
                    first_name=reg_data.get('first_name'),
                    last_name=reg_data.get('last_name'),
                    user_type='provider' if role in ['doctor', 'provider'] else 'patient',
                    is_approved=role == 'patient'
                )
                
                if role in ['doctor', 'provider']:
                    ServiceProvider.objects.create(
                        user=user,
                        provider_type=reg_data.get('provider_type', 'doctor' if role == 'doctor' else 'pharmacy'),
                        business_name=reg_data.get('business_name', f"{user.first_name} {user.last_name}"),
                        license_number=reg_data.get('license_number', reg_data.get('registration_number', '')),
                        specialization=reg_data.get('specialization', ''),
                        city=reg_data.get('state', '') # Frontend uses 'state' as city/region
                    )
                
                user.is_email_verified = True
                user.save()
            else:
                user_id = request.session.get('otp_user_id')
                user = User.objects.get(id=user_id)
            
            # Clear session
            del request.session['otp']
            request.session.pop('otp_type', None)
            request.session.pop('otp_user_id', None)
            request.session.pop('temp_reg_data', None)
            
            token = generate_token(user)
            
            return JsonResponse({
                'success': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': 'provider' if hasattr(user, 'serviceprovider') else 'patient'
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
