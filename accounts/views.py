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
    return render(request, 'core/react_app.html', {'page': 'Login'})

def provider_login_view(request):
    return redirect('login')

def logout_view(request):
    logout(request)
    return redirect('home')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/react_app.html', {'page': 'Register'})

def enter_mobile(request):
    return redirect('register')

def register_provider(request):
    return redirect('register')

def verify_otp(request):
    return render(request, 'core/react_app.html', {'page': 'VerifyOTP'})

def forgot_password(request):
    return render(request, 'core/react_app.html', {'page': 'ForgotPassword'})

def verify_email(request, token):
    try:
        user = User.objects.get(verification_token=token)
        user.is_email_verified = True
        user.verification_token = None
        user.save()
        messages.success(request, 'Email verified successfully!')
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    return redirect('login')
