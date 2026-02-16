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
@login_required
def admin_dashboard(request):
    """
    Admin dashboard showing system-wide statistics and recent activity.
    """
    if not is_admin(request.user):
        return render(request, '403.html', status=403)

    total_users = User.objects.count()
    total_patients = User.objects.filter(user_type='patient').count()
    total_providers = User.objects.filter(user_type='provider').count()
    pending_approvals = User.objects.filter(is_approved=False, user_type='provider').count()
    total_records = HealthRecord.objects.count()
    
    recent_users = User.objects.order_by('-created_at')[:5]
    recent_activities = ActivityLog.objects.select_related('user')[:10]
    pending_registrations = User.objects.filter(is_approved=False)[:5]
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    new_users_this_week = User.objects.filter(created_at__date__gte=week_ago).count()
    
    context = {
        'total_users': total_users,
        'total_patients': total_patients,
        'total_providers': total_providers,
        'pending_approvals': pending_approvals,
        'total_records': total_records,
        'recent_users': recent_users,
        'recent_activities': recent_activities,
        'pending_registrations': pending_registrations,
        'new_users_this_week': new_users_this_week,
    }
    return render(request, 'admin_portal/dashboard.html', context)

@login_required
def admin_users(request):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    user_type_filter = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '')
    
    users = User.objects.all()
    
    if user_type_filter != 'all':
        users = users.filter(user_type=user_type_filter)
    
    if search_query:
        users = users.filter(
            username__icontains=search_query
        ) | users.filter(
            email__icontains=search_query
        ) | users.filter(
            first_name__icontains=search_query
        )
    
    context = {
        'users': users,
        'user_type_filter': user_type_filter,
        'search_query': search_query,
    }
    return render(request, 'admin_portal/users.html', context)

@login_required
def admin_user_detail(request, user_id):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    user = get_object_or_404(User, id=user_id)
    health_records = HealthRecord.objects.filter(user=user)[:10]
    activities = ActivityLog.objects.filter(user=user)[:20]
    
    context = {
        'profile_user': user,
        'health_records': health_records,
        'activities': activities,
    }
    return render(request, 'admin_portal/user_detail.html', context)

@login_required
def admin_approve_user(request, user_id):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    ActivityLog.objects.create(
        user=request.user,
        action='user_approved',
        details=f'Approved user: {user.username}'
    )
    messages.success(request, f'User {user.username} has been approved')
    return redirect('admin_users')

@login_required
def admin_reject_user(request, user_id):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    ActivityLog.objects.create(
        user=request.user,
        action='user_rejected',
        details=f'Rejected and deleted user: {username}'
    )
    messages.success(request, f'User {username} has been rejected and removed')
    return redirect('admin_users')

@login_required
def admin_delete_user(request, user_id):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        ActivityLog.objects.create(
            user=request.user,
            action='user_deleted',
            details=f'Deleted user: {username}'
        )
        messages.success(request, f'User {username} has been deleted')
        return redirect('admin_users')
    return render(request, 'admin_portal/confirm_delete.html', {'profile_user': user})

@login_required
def admin_providers(request):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    providers = ServiceProvider.objects.select_related('user').all()
    context = {'providers': providers}
    return render(request, 'admin_portal/providers.html', context)

@login_required
def admin_health_data(request):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    records = HealthRecord.objects.select_related('user').order_by('-created_at')[:100]
    
    stats = {
        'total_records': HealthRecord.objects.count(),
        'total_medicines': Medicine.objects.count(),
        'total_prescriptions': Prescription.objects.count(),
        'total_policies': InsurancePolicy.objects.count(),
    }
    
    context = {
        'records': records,
        'stats': stats,
    }
    return render(request, 'admin_portal/health_data.html', context)

@login_required
def admin_reports(request):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    
    user_registrations = User.objects.filter(
        created_at__date__gte=month_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    health_records_by_month = HealthRecord.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(count=Count('id')).order_by('-month')[:6]
    
    user_type_distribution = User.objects.values('user_type').annotate(count=Count('id'))
    
    reg_labels = [item['date'].strftime('%Y-%m-%d') for item in user_registrations]
    reg_data = [item['count'] for item in user_registrations]
    
    health_labels = [item['month'].strftime('%b %Y') if item['month'] else 'Unknown' for item in health_records_by_month]
    health_data = [item['count'] for item in health_records_by_month]
    
    type_labels = [item['user_type'] or 'Unknown' for item in user_type_distribution]
    type_data = [item['count'] for item in user_type_distribution]
    
    context = {
        'user_registrations': list(user_registrations),
        'health_records_by_month': list(health_records_by_month),
        'user_type_distribution': list(user_type_distribution),
        'reg_labels_json': json.dumps(reg_labels),
        'reg_data_json': json.dumps(reg_data),
        'health_labels_json': json.dumps(health_labels),
        'health_data_json': json.dumps(health_data),
        'type_labels_json': json.dumps(type_labels),
        'type_data_json': json.dumps(type_data),
    }
    return render(request, 'admin_portal/reports.html', context)

@login_required
def admin_settings(request):
    if not is_admin(request.user):
        return render(request, '403.html', status=403)
    
    settings = SystemSettings.objects.all()
    
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        description = request.POST.get('description', '')
        
        if key and value:
            SystemSettings.objects.update_or_create(
                key=key,
                defaults={'value': value, 'description': description}
            )
            messages.success(request, 'Setting saved successfully')
        else:
            messages.error(request, 'Key and value are required')
        return redirect('admin_settings')
    
    context = {'settings': settings}
    return render(request, 'admin_portal/settings.html', context)
