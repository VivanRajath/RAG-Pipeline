# urls.py
from django.urls import path, include
from . import views
from .views import CustomLogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('file/<int:file_id>/', views.chat_view, name='chat'),


    path('accounts/logout/', CustomLogoutView.as_view(), name='account_logout'),


    path('accounts/', include('allauth.urls')),
]
