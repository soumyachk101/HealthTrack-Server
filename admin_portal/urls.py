from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('users/<int:user_id>/approve/', views.admin_approve_user, name='admin_approve_user'),
    path('users/<int:user_id>/reject/', views.admin_reject_user, name='admin_reject_user'),
    path('users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('providers/', views.admin_providers, name='admin_providers'),
    path('health-data/', views.admin_health_data, name='admin_health_data'),
    path('reports/', views.admin_reports, name='admin_reports'),
    path('settings/', views.admin_settings, name='admin_settings'),
]
