from django.urls import path
from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/dashboard/', api_views.dashboard_api, name='dashboard_api'),
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
