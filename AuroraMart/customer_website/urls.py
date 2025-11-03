from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('signup/', views.signup_page, name='signup'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.customer_home, name='customer_home'),
    path('cart/', views.cart_page, name='cart'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('profile/', views.profile_page, name='profile'),
    path('product/<str:sku>/', views.product_detail, name='product_detail'),
    path('about/', views.about_page, name='about'),
    path('products/', views.all_products, name='all_products'),
]