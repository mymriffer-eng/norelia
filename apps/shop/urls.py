from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Products
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search/', views.product_search, name='product_search'),
    
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
]
