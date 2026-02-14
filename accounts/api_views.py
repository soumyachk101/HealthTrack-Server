import json
import jwt
import datetime
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from .models import ServiceProvider, OTP
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
                # Generate OTP using the model
                otp_record = OTP.create_otp(user.email, 'login')
                otp = otp_record.otp_code
                
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
            
            # Store registration data in temporary storage (we'll use a dictionary as a simple cache)
            import uuid
            temp_id = str(uuid.uuid4())
            # In a real serverless environment, we'd use a cache like Redis
            # For now, we'll store in a simple in-memory dict (not suitable for production serverless)
            if not hasattr(register_api, 'temp_storage'):
                register_api.temp_storage = {}
            register_api.temp_storage[temp_id] = data
            
            # Generate OTP using the model
            otp_record = OTP.create_otp(email, 'register')
            otp = otp_record.otp_code
            
            # Send OTP email
            send_otp_email(email, otp, data.get('first_name'))
            
            # Store temp_id in session or return it to frontend to use later
            request.session['temp_reg_id'] = temp_id
            
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
            email = data.get('email')  # Need email to look up OTP
            otp_type = data.get('otp_type', 'register')  # Default to register
            
            # Validate OTP using the model
            otp_record = OTP.validate_otp(email, entered_otp, otp_type)
            if not otp_record:
                return JsonResponse({'success': False, 'error': 'Invalid or expired OTP'}, status=400)
            
            User = get_user_model()
            
            if otp_type == 'register':
                # Get registration data from our temporary storage
                temp_id = request.session.get('temp_reg_id')
                if not temp_id or not hasattr(register_api, 'temp_storage') or temp_id not in register_api.temp_storage:
                    return JsonResponse({'success': False, 'error': 'Registration session expired'}, status=400)
                
                reg_data = register_api.temp_storage[temp_id]
                # Clean up temporary storage
                del register_api.temp_storage[temp_id]
                request.session.pop('temp_reg_id', None)
                
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
            else:  # login case
                user = User.objects.get(email=email)
            
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

@csrf_exempt
def resend_otp_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            otp_type = data.get('otp_type', 'register')
            email = data.get('email')
            first_name = data.get('first_name', '')
            
            if not email:
                return JsonResponse({'success': False, 'error': 'Email is required to resend OTP.'}, status=400)
            
            # Generate new OTP using the model
            otp_record = OTP.create_otp(email, otp_type)
            otp = otp_record.otp_code
            
            # Send OTP email
            send_otp_email(email, otp, first_name)
            
            return JsonResponse({
                'success': True,
                'message': 'A new verification code has been sent to your email'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
