from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginview.as_view(), name='main_page'),
    path('signup/', views.signupview.as_view(), name='signup'),
    path('login/', views.loginview.as_view(), name='login'),
    #add middleware to protect these routes
    path('new_user/', views.new_userview.as_view(), name='new_user'),
    path('home/', views.mainpageview.as_view(), name='customer_home'),
    path('cart/', views.cartview.as_view(), name='cart'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('profile/', views.profile_page, name='profile'),
    path('product/<str:sku>/', views.product_detailview.as_view(), name='product_detail'),
    path('about/', views.about_page, name='about'),
    path('products/', views.all_productsview.as_view(), name='all_products'),
    path('search/ajax/', views.search_ajax_view.as_view(), name='search_ajax'),
]