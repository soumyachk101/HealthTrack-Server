from django.urls import path
from . import views, api_views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login/provider/', views.provider_login_view, name='provider_login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('register/provider/', views.register_provider, name='register_provider'),
    path('enter-mobile/', views.enter_mobile, name='enter_mobile'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    
    # API endpoints for SPA
    path('api/login/', api_views.login_api, name='api_login'),
    path('api/register/', api_views.register_api, name='api_register'),
    path('api/verify-otp/', api_views.verify_otp_api, name='api_verify_otp'),
    path('api/resend-otp/', api_views.resend_otp_api, name='api_resend_otp'),
]

