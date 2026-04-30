from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db.models import Avg

from .models import (
    HealthRecord, Medicine, Prescription, MentalHealthLog,
    InsurancePolicy, LifestyleLog, ActivityLog
)
from .forms import MedicineForm, HealthRecordForm, PrescriptionForm

def home(request):
    """
    Landing page view. Serves the React app.
    """
    if request.user.is_authenticated:
        if request.user.is_admin_user:
            return redirect('admin_dashboard')
        elif request.user.user_type == 'provider':
            return redirect('provider_dashboard')
        return redirect('dashboard')
    
    return render(request, 'core/react_app.html', {
        'page': 'Landing',
        'debug': settings.DEBUG
    })

@login_required
def provider_dashboard(request):
    """
    Dashboard for Service Providers.
    """
    if request.user.user_type != 'provider' and request.user.user_type != 'doctor':
        return redirect('dashboard')
    return render(request, 'core/react_app.html', {
        'page': 'DoctorDashboard' if request.user.user_type == 'doctor' else 'ProviderDashboard',
        'debug': settings.DEBUG
    })

@login_required
def dashboard(request):
    """
    Main user dashboard showing summary of health specs.
    """
    return render(request, 'core/react_app.html', {
        'page': 'Dashboard',
        'debug': settings.DEBUG
    })

@login_required
def medicines(request):
    return render(request, 'core/react_app.html', {'page': 'Medicines', 'debug': settings.DEBUG})

@login_required
def add_medicine(request):
    return render(request, 'core/react_app.html', {'page': 'AddMedicine', 'debug': settings.DEBUG})

@login_required
def health_track(request):
    return render(request, 'core/react_app.html', {'page': 'HealthTrack', 'debug': settings.DEBUG})

@login_required
def add_health_record(request):
    return render(request, 'core/react_app.html', {'page': 'AddHealthRecord', 'debug': settings.DEBUG})

@login_required
def mental_health(request):
    return render(request, 'core/react_app.html', {'page': 'MentalHealth', 'debug': settings.DEBUG})

@login_required
def prescriptions(request):
    return render(request, 'core/react_app.html', {'page': 'Prescriptions', 'debug': settings.DEBUG})

@login_required
def add_prescription(request):
    return render(request, 'core/react_app.html', {'page': 'AddPrescription', 'debug': settings.DEBUG})

@login_required
def lifestyle(request):
    return render(request, 'core/react_app.html', {'page': 'Lifestyle', 'debug': settings.DEBUG})

@login_required
def insurance(request):
    return render(request, 'core/react_app.html', {'page': 'Insurance', 'debug': settings.DEBUG})

@login_required
def past_records(request):
    return render(request, 'core/react_app.html', {'page': 'PastRecords', 'debug': settings.DEBUG})

@login_required
def profile(request):
    return render(request, 'core/react_app.html', {'page': 'Profile', 'debug': settings.DEBUG})

