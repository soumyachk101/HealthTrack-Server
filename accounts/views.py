import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, ServiceProvider
from core.models import ActivityLog
from core.utils import send_verification_email

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_admin_user:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not user.is_email_verified:
                messages.error(request, 'Please verify your email address to login.')
                return render(request, 'accounts/login.html')

            login(request, user)
            ActivityLog.objects.create(
                user=user,
                action='login',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            if user.is_admin_user:
                return redirect('admin_dashboard')
            elif user.user_type == 'provider':
                return redirect('provider_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')

def provider_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_provider:
            return redirect('provider_dashboard')
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.user_type != 'provider':
                messages.error(request, 'This login is for service providers only.')
                return render(request, 'accounts/provider_login.html')
            
            if not user.is_email_verified:
                messages.error(request, 'Please verify your email address to login.')
                return render(request, 'accounts/provider_login.html')

            login(request, user)
            ActivityLog.objects.create(
                user=user,
                action='provider_login',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return redirect('provider_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/provider_login.html')

def logout_view(request):
    if request.user.is_authenticated:
        try:
            ActivityLog.objects.create(
                user=request.user,
                action='logout',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            print(f"Error logging logout activity: {e}")
    logout(request)
    return redirect('home')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Get role from POST data or URL parameter
    role = request.POST.get('role') or request.GET.get('role', 'patient')
    
    if request.method == 'POST':
        data = request.POST
        password = data.get('password')
        password2 = data.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'accounts/register.html', {'role': role})
        
        if User.objects.filter(username=data.get('username')).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'accounts/register.html', {'role': role})
        
        if User.objects.filter(email=data.get('email')).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'accounts/register.html', {'role': role})
        
        # Determine user_type based on role
        if role == 'doctor':
            user_type = 'provider'
            provider_type = 'doctor'
            is_approved = False  # Doctors need approval
        elif role == 'service_provider':
            user_type = 'provider'
            provider_type = data.get('provider_type', 'pharmacy')  # Default to pharmacy
            is_approved = False  # Service providers need approval
        else:
            user_type = 'patient'
            provider_type = None
            is_approved = True  # Patients are auto-approved
            
        # Store registration data in session
        temp_reg_data = {
            'username': data.get('username'),
            'email': data.get('email'),
            'password': password,
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'state': data.get('state', ''),
            'user_type': user_type,
            'is_approved': is_approved
        }
        
        # Add provider-specific fields if needed
        if user_type == 'provider':
            temp_reg_data['provider_type'] = provider_type
            temp_reg_data['specialization'] = data.get('specialization', '')
            temp_reg_data['registration_number'] = data.get('registration_number', '')
            temp_reg_data['license_number'] = data.get('license_number', '')
            temp_reg_data['business_name'] = data.get('business_name', data.get('first_name', '') + ' ' + data.get('last_name', ''))
        
        request.session['temp_reg_data'] = temp_reg_data
        
        # Generate OTP and send via email
        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        request.session['verification_email'] = data.get('email')
        
        # Import and send OTP email
        from core.utils import send_otp_email
        email_sent = send_otp_email(
            data.get('email'), 
            otp, 
            data.get('first_name')
        )
        
        if email_sent:
            messages.success(request, 'Verification code sent to your email!')
        else:
            messages.warning(request, 'Could not send email. Please check your email address.')
        
        return redirect('verify_otp')
    
    return render(request, 'accounts/register.html', {'role': role})

def enter_mobile(request):
    """Step 2: Enter mobile number and send OTP."""
    if not request.session.get('temp_reg_data'):
        return redirect('register')
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '')
        
        if not phone or len(phone) != 10:
            messages.error(request, 'Please enter a valid 10-digit mobile number')
            return render(request, 'accounts/enter_mobile.html')
        
        # Store phone in session
        request.session['temp_reg_data']['phone'] = phone
        request.session['verification_phone'] = phone
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        
        # In production, send SMS here
        print(f"OTP for {phone}: {otp}")
        
        return redirect('verify_otp')
    
    return render(request, 'accounts/enter_mobile.html')

def register_provider(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        data = request.POST
        password = data.get('password')
        password2 = data.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'accounts/register_provider.html')
        
        if User.objects.filter(username=data.get('username')).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'accounts/register_provider.html')
            
        # Store in session
        request.session['temp_reg_data'] = {
            'username': data.get('username'),
            'email': data.get('email'),
            'password': password,
            'phone': data.get('phone', ''),
            'city': data.get('state', ''),  # Using state field for city
            'address': data.get('address', ''),
            'user_type': 'provider',
            'is_approved': False,
            # Provider specific
            'business_name': data.get('business_name'),
            'provider_type': data.get('provider_type'),
            'license_number': data.get('license_number'),
            'specialization': data.get('specialization', ''),
            'working_hours': data.get('working_hours', ''),
            'services_offered': data.get('services_offered', '')
        }
        
        # Generate OTP and send via email
        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        request.session['verification_email'] = data.get('email')
        
        # Send OTP email
        from core.utils import send_otp_email
        email_sent = send_otp_email(
            data.get('email'),
            otp,
            data.get('business_name')
        )
        
        if email_sent:
            messages.success(request, 'Verification code sent to your email!')
        else:
            messages.warning(request, 'Could not send email. Please check your email address.')
        
        return redirect('verify_otp')
    
    return render(request, 'accounts/register_provider.html')

def verify_otp(request):
    if not request.session.get('temp_reg_data') or not request.session.get('otp'):
        return redirect('register')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        generated_otp = request.session.get('otp')
        
        if entered_otp == generated_otp:
            # OTP Verified - Create User
            data = request.session.get('temp_reg_data').copy()
            
            # Extract provider fields
            provider_fields = None
            if data.get('user_type') == 'provider':
                provider_fields = {
                    'business_name': data.pop('business_name', data.get('first_name', '') + ' ' + data.get('last_name', '')),
                    'provider_type': data.pop('provider_type', 'doctor'),
                    'license_number': data.pop('license_number', '') or data.pop('registration_number', ''),
                    'specialization': data.pop('specialization', ''),
                    'working_hours': data.pop('working_hours', ''),
                    'services_offered': data.pop('services_offered', ''),
                }
            
            # Remove provider-specific fields from user data
            data.pop('provider_type', None)
            data.pop('registration_number', None)
            data.pop('license_number', None)
            data.pop('specialization', None)
            data.pop('business_name', None)
            data.pop('working_hours', None)
            data.pop('services_offered', None)
            
            # Create User
            data['is_email_verified'] = True
            user = User.objects.create_user(**data)
            
            # Create Provider Profile if needed
            if data.get('user_type') == 'provider' and provider_fields:
                ServiceProvider.objects.create(user=user, **provider_fields)
                
            ActivityLog.objects.create(
                user=user,
                action='registration',
                details=f"New {data['user_type']} registration verified via OTP"
            )
            
            # Clean session
            del request.session['temp_reg_data']
            del request.session['otp']
            
            # Send email (optional now, since verified by phone)
            send_verification_email(user, request)
            
            if data['user_type'] == 'provider':
                messages.success(request, 'Registration verified! Please wait for admin approval.')
            else:
                messages.success(request, 'Account verified successfully! Please login.')
                
            return redirect('login')
            
        else:
            messages.error(request, 'Invalid OTP code. Please try again.')
            
    return render(request, 'accounts/verify_otp.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            messages.success(request, 'Password reset instructions sent to your email')
        else:
            messages.error(request, 'Email not found')
    
    return render(request, 'accounts/forgot_password.html')

def verify_email(request, token):
    try:
        user = User.objects.get(verification_token=token)
        user.is_email_verified = True
        user.verification_token = None
        user.save()
        messages.success(request, 'Email verified successfully! You can now login.')
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    
    return redirect('login')
