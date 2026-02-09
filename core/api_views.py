from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.views.decorators.http import require_GET
from django.utils.timesince import timesince

from .models import (
    HealthRecord, Medicine, Prescription, MentalHealthLog,
    InsurancePolicy, LifestyleLog, ActivityLog
)

@login_required
@require_GET
def dashboard_api(request):
    """
    API endpoint to return dashboard data as JSON.
    """
    user = request.user
    
    # Latest Health Record
    latest_record = HealthRecord.objects.filter(user=user).first()
    latest_record_data = None
    if latest_record:
        latest_record_data = {
            'blood_pressure_systolic': latest_record.blood_pressure_systolic,
            'blood_pressure_diastolic': latest_record.blood_pressure_diastolic,
            'bp_status': latest_record.bp_status,
            'blood_sugar': str(latest_record.blood_sugar) if latest_record.blood_sugar else None,
            'weight': str(latest_record.weight) if latest_record.weight else None,
            'heart_rate': latest_record.heart_rate,
            'recorded_at': latest_record.recorded_at.isoformat()
        }

    # Active Medicines
    active_medicines = Medicine.objects.filter(user=user, is_active=True).count()

    # Recent Activity
    recent_activities_qs = ActivityLog.objects.filter(user=user)[:5]
    recent_activities = []
    for activity in recent_activities_qs:
        recent_activities.append({
            'action': activity.get_action_display(),
            'action_display': activity.get_action_display(), # Frontend uses this
            'details': activity.details,
            'created_at': activity.created_at.isoformat(),
            'created_at_since': timesince(activity.created_at)
        })

    # Mental Health
    latest_mental_health = MentalHealthLog.objects.filter(user=user).first()
    mental_health_data = None
    if latest_mental_health:
        mental_health_data = {
            'sleep_hours': str(latest_mental_health.sleep_hours) if latest_mental_health.sleep_hours else None,
            'mood_score': latest_mental_health.mood_score,
            'stress_level': latest_mental_health.stress_level
        }

    data = {
        'user': {
            'name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'email': user.email
        },
        'latest_record': latest_record_data,
        'active_medicines': active_medicines,
        'active_medicines_count': active_medicines, # Redundant but safe for frontend interface
        'recent_activities': recent_activities,
        'latest_mental_health': mental_health_data
    }

    return JsonResponse(data)
