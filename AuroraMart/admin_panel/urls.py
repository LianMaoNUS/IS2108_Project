from django.urls import path
from .views import AdminDashboardView, AdminTableView, loginview, logoutview, profileSettingsView, signupview

urlpatterns = [
    path('login/', loginview.as_view(), name='admin_login'),
    path('signup/', signupview.as_view(), name='admin_signup'),
    path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),        # main dashboard
    path('list/', AdminTableView.as_view(), name='admin_list'), 
    path('logout/', logoutview, name='admin_logout'),
    path('profile/', profileSettingsView.as_view(), name='admin_profile'),
    path('', loginview.as_view(), name='admin_home'),  # default to login
]