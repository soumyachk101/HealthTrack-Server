from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg

from .models import (
    HealthRecord, Medicine, Prescription, MentalHealthLog,
    InsurancePolicy, LifestyleLog, ActivityLog
)
from .forms import MedicineForm, HealthRecordForm, PrescriptionForm

def home(request):
    """
    Landing page view. Redirects authenticated users to their dashboard.
    """
    if request.user.is_authenticated:
        if request.user.is_admin_user:
            return redirect('admin_dashboard')
        elif request.user.user_type == 'provider':
            return redirect('provider_dashboard')
        return redirect('dashboard')
    return JsonResponse({
        "status": "success",
        "message": "HealthTrack Backend is running successfully.",
        "version": "1.0.0"
    })

@login_required
def provider_dashboard(request):
    """
    Dashboard for Service Providers.
    """
    if request.user.user_type != 'provider':
        return redirect('dashboard')
    return render(request, 'core/provider_dashboard.html')

@login_required
def dashboard(request):
    """
    Main user dashboard showing summary of health specs.
    """
    latest_record = HealthRecord.objects.filter(user=request.user).first()
    active_medicines = Medicine.objects.filter(user=request.user, is_active=True).count()
    recent_activities = ActivityLog.objects.filter(user=request.user)[:5]
    latest_mental_health = MentalHealthLog.objects.filter(user=request.user).first()
    
    context = {
        'latest_record': latest_record,
        'active_medicines': active_medicines,
        'recent_activities': recent_activities,
        'latest_mental_health': latest_mental_health,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def medicines(request):
    medicines = Medicine.objects.filter(user=request.user)
    active_count = medicines.filter(is_active=True).count()
    context = {
        'medicines': medicines,
        'active_count': active_count,
    }
    return render(request, 'core/medicines.html', context)

@login_required
def add_medicine(request):
    """
    View to add a new medicine entry.
    """
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save(commit=False)
            medicine.user = request.user
            medicine.save()
            ActivityLog.objects.create(
                user=request.user,
                action='medicine_added',
                details=f"Added medicine: {medicine.name}"
            )
            messages.success(request, 'Medicine added successfully')
            return redirect('medicines')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = MedicineForm()
    return render(request, 'core/add_medicine.html', {'form': form})

@login_required
def health_track(request):
    records = HealthRecord.objects.filter(user=request.user)[:30]
    context = {'records': records}
    return render(request, 'core/health_track.html', context)

@login_required
def add_health_record(request):
    """
    View to process and save a new health record.
    """
    if request.method == 'POST':
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            ActivityLog.objects.create(
                user=request.user,
                action='record_added',
                details='Added new health record'
            )
            messages.success(request, 'Health record added successfully')
            return redirect('health_track')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = HealthRecordForm()
    return render(request, 'core/add_health_record.html', {'form': form})

@login_required
def mental_health(request):
    """
    Displays mental health logs and average mood score.
    """
    logs = MentalHealthLog.objects.filter(user=request.user)[:30]
    avg_mood = logs.aggregate(Avg('mood_score'))['mood_score__avg'] or 0
    context = {
        'logs': logs,
        'avg_mood': round(avg_mood, 1),
    }
    return render(request, 'core/mental_health.html', context)

@login_required
def prescriptions(request):
    prescriptions = Prescription.objects.filter(user=request.user)
    context = {'prescriptions': prescriptions}
    return render(request, 'core/prescriptions.html', context)

@login_required
def add_prescription(request):
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, request.FILES)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.user = request.user
            prescription.save()
            ActivityLog.objects.create(
                user=request.user,
                action='prescription_added',
                details=f"Added prescription from {prescription.doctor_name}"
            )
            messages.success(request, 'Prescription added successfully')
            return redirect('prescriptions')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PrescriptionForm()
    return render(request, 'core/add_prescription.html', {'form': form})

@login_required
def lifestyle(request):
    logs = LifestyleLog.objects.filter(user=request.user)[:30]
    context = {'logs': logs}
    return render(request, 'core/lifestyle.html', context)

@login_required
def insurance(request):
    """
    Lists user's insurance policies and their status.
    """
    policies = InsurancePolicy.objects.filter(user=request.user)
    active_policies = policies.filter(is_active=True).count()
    context = {
        'policies': policies,
        'active_policies': active_policies,
    }
    return render(request, 'core/insurance.html', context)

@login_required
def past_records(request):
    health_records = HealthRecord.objects.filter(user=request.user)
    prescriptions = Prescription.objects.filter(user=request.user)
    context = {
        'health_records': health_records,
        'prescriptions': prescriptions,
    }
    return render(request, 'core/past_records.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.city = request.POST.get('city', user.city)
        user.blood_group = request.POST.get('blood_group', user.blood_group)
        user.emergency_contact = request.POST.get('emergency_contact', user.emergency_contact)
        user.emergency_phone = request.POST.get('emergency_phone', user.emergency_phone)
        user.save()
        
        ActivityLog.objects.create(
            user=user,
            action='profile_updated',
            details='Profile information updated'
        )
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')
    
    return render(request, 'core/profile.html')

