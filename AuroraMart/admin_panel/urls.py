from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginview.as_view(), name='admin_login'),
    path('login/', views.loginview.as_view(), name='admin_login'),
    path('signup/', views.signupview.as_view(), name='admin_signup'),
    path('admin_panel/', views.dashboardview.as_view(), name='admin_dashboard'),
<<<<<<< HEAD
    path('ajax/get-subcategories/', views.get_subcategories, name='get_subcategories'),
=======
>>>>>>> 22aa262936ccb0cc0fa0b2c51c017d722aef8917
]