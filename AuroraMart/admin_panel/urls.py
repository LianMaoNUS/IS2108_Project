# admin_panel/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginview.as_view(), name='admin_login'),
    path('signup/', views.signupview.as_view(), name='admin_signup'),
    path('dashboard/', views.dashboardview.as_view(), name='admin_dashboard'),
]