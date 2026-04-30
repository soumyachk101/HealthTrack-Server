from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.models import User, ServiceProvider
from core.models import HealthRecord, ActivityLog

from django.views.decorators.csrf import csrf_exempt
from accounts.api_views import jwt_required

def admin_required(view_func):
    @jwt_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_admin_user:
            return JsonResponse({'success': False, 'error': 'Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@csrf_exempt
@admin_required
def admin_stats_api(request):
    print(f"DEBUG: Admin Stats API called by {request.user.email}")
    total_users = User.objects.count()
    patients = User.objects.filter(user_type='patient').count()
    providers = User.objects.filter(user_type__in=['doctor', 'provider']).count()
    pending_approvals = User.objects.filter(is_approved=False, user_type__in=['doctor', 'provider']).count()
    total_records = HealthRecord.objects.count()

    return JsonResponse({
        'success': True,
        'stats': {
            'total_users': total_users,
            'patients': patients,
            'providers': providers,
            'pending_approvals': pending_approvals,
            'total_records': total_records,
        }
    })

@csrf_exempt
@admin_required
def admin_users_api(request):
    print(f"DEBUG: Admin Users API called with params: {request.GET}")
    user_type = request.GET.get('type')
    search = request.GET.get('search')
    
    users = User.objects.all().order_by('-date_joined')
    
    if user_type:
        users = users.filter(user_type=user_type)
    if search:
        users = users.filter(email__icontains=search) | users.filter(username__icontains=search)
    
    user_list = []
    for user in users:
        # Determine specific role
        display_role = user.user_type
        if user.user_type == 'provider' and hasattr(user, 'provider_profile'):
            display_role = user.provider_profile.provider_type
            
        user_list.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'user_type': display_role,
            'is_approved': user.is_approved,
            'date_joined': user.date_joined.strftime('%Y-%m-%d'),
        })
        
    return JsonResponse({
        'success': True,
        'users': user_list
    })

@csrf_exempt
@admin_required
def admin_user_action_api(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        
    import json
    data = json.loads(request.body)
    action = data.get('action')
    
    try:
        user = User.objects.get(id=user_id)
        if action == 'approve':
            user.is_approved = True
            user.save()
            ActivityLog.objects.create(user=request.user, action='admin_action', details=f"Approved user {user.email}")
        elif action == 'reject':
            user.is_approved = False
            user.save()
            ActivityLog.objects.create(user=request.user, action='admin_action', details=f"Rejected user {user.email}")
        elif action == 'delete':
            email = user.email
            user.delete()
            ActivityLog.objects.create(user=request.user, action='admin_action', details=f"Deleted user {email}")
            
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
