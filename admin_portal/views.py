from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from datetime import timedelta
import json

from accounts.models import User, ServiceProvider
from core.models import (
    HealthRecord, Medicine, Prescription, InsurancePolicy, ActivityLog, SystemSettings
)

def is_admin(user):
    return user.is_authenticated and (user.is_admin_user or user.is_superuser)

@login_required
def admin_dashboard(request):
    """
    Admin dashboard showing system-wide statistics and recent activity.
    """
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    return render(request, 'core/react_app.html', {'page': 'AdminDashboard'})

@login_required
def admin_users(request):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    return render(request, 'core/react_app.html', {'page': 'AdminUsers'})

@login_required
def admin_user_detail(request, user_id):
    return redirect('admin_users') # Let React handle selection

@login_required
def admin_approve_user(request, user_id):
    return redirect('admin_users')

@login_required
def admin_reject_user(request, user_id):
    return redirect('admin_users')

@login_required
def admin_delete_user(request, user_id):
    return redirect('admin_users')

@login_required
def admin_providers(request):
    return redirect('admin_dashboard')

@login_required
def admin_health_data(request):
    return render(request, 'core/react_app.html', {'page': 'AdminHealthData'})

@login_required
def admin_reports(request):
    return render(request, 'core/react_app.html', {'page': 'AdminReports'})

@login_required
def admin_settings(request):
    return render(request, 'core/react_app.html', {'page': 'AdminSettings'})
