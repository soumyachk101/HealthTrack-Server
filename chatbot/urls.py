from django.urls import path
from . import views

urlpatterns = [
    path('api/', views.chat_api, name='chat_api'),
    path('api/tts/', views.tts_api, name='tts_api'),
]
