"""
URLs for the accounts app
"""
from django.urls import path
from . import views

# No namespace here as it might conflict with allauth
urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('change-role/', views.change_role, name='change_role'),
]