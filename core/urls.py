from django.urls import path
from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/dashboard/', api_views.dashboard_api, name='dashboard_api'),
    path('api/health-track/add/', api_views.add_health_record_api, name='add_health_record_api'),
    path('api/medicines/add/', api_views.add_medicine_api, name='add_medicine_api'),
    path('api/prescriptions/add/', api_views.add_prescription_api, name='add_prescription_api'),
    
    # Getter APIs
    path('api/medicines/', api_views.medicines_api, name='medicines_api'),
    path('api/health-track/', api_views.health_track_api, name='health_track_api'),
    path('api/prescriptions/', api_views.prescriptions_api, name='prescriptions_api'),
    path('api/profile/', api_views.profile_api, name='profile_api'),
    path('api/mental-health/', api_views.mental_health_api, name='mental_health_api'),
    path('api/lifestyle/', api_views.lifestyle_api, name='lifestyle_api'),
    path('api/insurance/', api_views.insurance_api, name='insurance_api'),
    path('api/past-records/', api_views.past_records_api, name='past_records_api'),
    path('api/appointments/', api_views.appointments_api, name='appointments_api'),
    path('api/appointments/<int:appointment_id>/action/', api_views.appointment_action_api, name='appointment_action_api'),
    path('api/service-requests/', api_views.service_requests_api, name='service_requests_api'),
    path('api/service-requests/<int:request_id>/action/', api_views.service_request_action_api, name='service_request_action_api'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('provider-dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('medicines/', views.medicines, name='medicines'),
    path('medicines/add/', views.add_medicine, name='add_medicine'),
    path('health-track/', views.health_track, name='health_track'),
    path('health-track/add/', views.add_health_record, name='add_health_record'),
    path('mental-health/', views.mental_health, name='mental_health'),
    path('prescriptions/', views.prescriptions, name='prescriptions'),
    path('prescriptions/add/', views.add_prescription, name='add_prescription'),
    path('lifestyle/', views.lifestyle, name='lifestyle'),
    path('insurance/', views.insurance, name='insurance'),
    path('past-records/', views.past_records, name='past_records'),
    path('profile/', views.profile, name='profile'),
    
]
