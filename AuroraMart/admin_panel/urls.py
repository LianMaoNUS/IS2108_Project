# admin_panel/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='admin_login'),
    path('signup/', views.signup, name='admin_signup'),
    path('home/', views.index, name='admin_index'),
]