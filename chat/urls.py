from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('file/<int:file_id>/', views.chat_view, name='chat'),

    
]
