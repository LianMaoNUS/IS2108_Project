from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginview.as_view(), name='main_page'),
    path('signup/', views.signupview.as_view(), name='signup'),
    path('login/', views.loginview.as_view(), name='login'),
    #add middleware to protect these routes
    path('new_user/', views.new_userview.as_view(), name='new_user'),
<<<<<<< HEAD
    path('home/', views.mainpageview.as_view(), name='customer_home'),
=======
    path('home/', views.customer_home, name='customer_home'),
>>>>>>> 22aa262936ccb0cc0fa0b2c51c017d722aef8917
    path('cart/', views.cart_page, name='cart'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('profile/', views.profile_page, name='profile'),
    path('product/<str:sku>/', views.product_detail, name='product_detail'),
    path('about/', views.about_page, name='about'),
    path('products/', views.all_products, name='all_products'),
]