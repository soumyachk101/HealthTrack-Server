from django.http import JsonResponse
from django.db.models import Avg
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils.timesince import timesince

from accounts.api_views import jwt_required

from .models import (
    HealthRecord, Medicine, Prescription, MentalHealthLog,
    InsurancePolicy, LifestyleLog, ActivityLog
)

@csrf_exempt
@jwt_required
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

@csrf_exempt
@jwt_required
def add_health_record_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    import json
    try:
        data = json.loads(request.body)
        user = request.user
        
        # Create HealthRecord
        HealthRecord.objects.create(
            user=user,
            blood_pressure_systolic=data.get('blood_pressure_systolic') or None,
            blood_pressure_diastolic=data.get('blood_pressure_diastolic') or None,
            blood_sugar=data.get('blood_sugar') or None,
            weight=data.get('weight') or None,
            heart_rate=data.get('heart_rate') or None,
            temperature=data.get('temperature') or None,
            oxygen_level=data.get('oxygen_level') or None,
            notes=data.get('notes', '')
        )
        
        # Check for activity log if needed, or rely on signals
        # For now, just return success
        return JsonResponse({'message': 'Health record added successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@jwt_required
def add_medicine_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    import json
    from datetime import datetime
    try:
        data = json.loads(request.body)
        user = request.user
        
        start_date = data.get('start_date')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
        end_date = data.get('end_date')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = None

        Medicine.objects.create(
            user=user,
            name=data.get('name'),
            dosage=data.get('dosage'),
            frequency=data.get('frequency'),
            prescribed_by=data.get('prescribed_by', ''),
            start_date=start_date,
            end_date=end_date,
            notes=data.get('notes', '')
        )
        
        return JsonResponse({'message': 'Medicine added successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@jwt_required
def add_prescription_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    import json
    try:
        # data = json.loads(request.body) 
        # For prescriptions, we might be uploading files.
        # But for now, let's assume JSON for simplicity or handle multipart if needed.
        # If the frontend sends JSON (no file), we use json.loads.
        # If the frontend uses FormData with file, we need request.POST and request.FILES.
        
        # Checking content type
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            user = request.user
            Prescription.objects.create(
                user=user,
                doctor_name=data.get('doctor_name'),
                hospital_name=data.get('hospital_name'),
                notes=data.get('notes', '')
                # image handling to be added if needed
            )
        else:
            # Multipart form data
            user = request.user
            doctor_name = request.POST.get('doctor_name')
            hospital_name = request.POST.get('hospital_name')
            notes = request.POST.get('notes', '')
            image = request.FILES.get('image')
            
            Prescription.objects.create(
                user=user,
                doctor_name=doctor_name,
                hospital_name=hospital_name,
                notes=notes,
                image=image
            )

        return JsonResponse({'message': 'Prescription added successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@jwt_required
@require_GET
def medicines_api(request):
    user = request.user
    medicines = Medicine.objects.filter(user=user).order_by('-created_at')
    
    meds_data = []
    for med in medicines:
        meds_data.append({
            'name': med.name,
            'dosage': med.dosage,
            'frequency_display': med.get_frequency_display(),
            'start_date': med.start_date.isoformat() if med.start_date else None,
            'end_date': med.end_date.isoformat() if med.end_date else None,
            'is_active': med.is_active
        })

    active_count = medicines.filter(is_active=True).count()

    return JsonResponse({
        'medicines': meds_data,
        'active_count': active_count
    })

@csrf_exempt
@jwt_required
@require_GET
def health_track_api(request):
    user = request.user
    records = HealthRecord.objects.filter(user=user).order_by('-recorded_at')
    
    data = []
    for record in records:
        data.append({
            'recorded_at': record.recorded_at.strftime('%Y-%m-%d %H:%M'),
            'blood_pressure_systolic': record.blood_pressure_systolic,
            'blood_pressure_diastolic': record.blood_pressure_diastolic,
            'blood_sugar': str(record.blood_sugar) if record.blood_sugar else None,
            'weight': str(record.weight) if record.weight else None,
            'heart_rate': record.heart_rate,
            'oxygen_level': str(record.oxygen_level) if record.oxygen_level else None,
            'bp_status': record.bp_status
        })
        
    return JsonResponse({'records': data})

@csrf_exempt
@jwt_required
@require_GET
def prescriptions_api(request):
    user = request.user
    prescriptions = Prescription.objects.filter(user=user).order_by('-created_at')
    
    data = []
    for p in prescriptions:
        data.append({
            'prescription_date': p.created_at.strftime('%Y-%m-%d'), # Using created_at as prescription date for simpler logic
            'doctor_name': p.doctor_name,
            'hospital_name': p.hospital_name,
            'diagnosis': p.notes[:50] + '...' if len(p.notes) > 50 else p.notes, # Using notes as diagnosis placeholder
            'follow_up_date': None # Add this field to model if needed
        })
        
    return JsonResponse({'prescriptions': data})

@csrf_exempt
@jwt_required
@require_GET
def profile_api(request):
    user = request.user
    
    # Mock messages for now, or fetch from a persistent store
    messages = [
        {'tags': 'success', 'message': f'Welcome back, {user.username}!'}
    ]

    profile_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        # Add other fields if extended User model has them, otherwise defaulting to empty
        'phone': getattr(user, 'phone', ''),
        'city': getattr(user, 'city', ''),
        'blood_group': getattr(user, 'blood_group', ''),
        'address': getattr(user, 'address', ''),
        'emergency_contact': getattr(user, 'emergency_contact', ''),
        'emergency_phone': getattr(user, 'emergency_phone', ''),
    }

    return JsonResponse({
        'user': profile_data,
        'messages': messages,
        'csrf_token': get_token(request)
    })

@csrf_exempt
@jwt_required
@require_GET
def mental_health_api(request):
    user = request.user
    logs = MentalHealthLog.objects.filter(user=user).order_by('-recorded_at')
    
    # Calculate average mood
    avg_mood = logs.aggregate(models.Avg('mood_score'))['mood_score__avg'] or 0
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'recorded_at': log.recorded_at.strftime('%Y-%m-%d %H:%M'),
            'mood_score': log.mood_score,
            'mood_score_display': log.get_mood_score_display(),
            'stress_level_display': log.get_stress_level_display(),
            'sleep_hours': float(log.sleep_hours) if log.sleep_hours else None,
            'notes': log.notes
        })

    return JsonResponse({
        'avg_mood': round(avg_mood, 1),
        'logs': logs_data
    })

@csrf_exempt
@jwt_required
@require_GET
def lifestyle_api(request):
    user = request.user
    logs = LifestyleLog.objects.filter(user=user).order_by('-recorded_at')
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'recorded_at': log.recorded_at.isoformat(),
            'water_intake': log.water_intake,
            'exercise_minutes': log.exercise_minutes,
            'steps_count': log.steps_count,
            'calories_consumed': log.calories_consumed
        })

    return JsonResponse({
        'logs': logs_data
    })

@csrf_exempt
@jwt_required
@require_GET
def insurance_api(request):
    user = request.user
    policies = InsurancePolicy.objects.filter(user=user).order_by('-created_at')
    
    policies_data = []
    for policy in policies:
        policies_data.append({
            'provider_name': policy.provider_name,
            'policy_type_display': policy.get_policy_type_display(),
            'policy_number': policy.policy_number,
            'coverage_amount': float(policy.coverage_amount),
            'end_date': policy.end_date.isoformat(),
            'is_active': policy.is_active
        })

    active_policies = policies.filter(is_active=True).count()

    return JsonResponse({
        'policies': policies_data,
        'active_policies': active_policies
    })

@csrf_exempt
@jwt_required
@require_GET
def past_records_api(request):
    user = request.user
    health_records = HealthRecord.objects.filter(user=user).order_by('-recorded_at')
    prescriptions = Prescription.objects.filter(user=user).order_by('-prescription_date')
    
    health_data = []
    for record in health_records:
        health_data.append({
            'recorded_at': record.recorded_at.strftime('%Y-%m-%d'),
            'blood_pressure_systolic': record.blood_pressure_systolic,
            'blood_pressure_diastolic': record.blood_pressure_diastolic
        })

    prescription_data = []
    for p in prescriptions:
        prescription_data.append({
            'prescription_date': p.prescription_date.isoformat(),
            'doctor_name': p.doctor_name
        })

    return JsonResponse({
        'health_records': health_data,
        'prescriptions': prescription_data
    })
