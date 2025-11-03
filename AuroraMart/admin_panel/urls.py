from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginview.as_view(), name='admin_login'),
    path('login/', views.loginview.as_view(), name='admin_login'),
    path('signup/', views.signupview.as_view(), name='admin_signup'),
    path('admin_panel/', views.dashboardview.as_view(), name='admin_dashboard'),
]