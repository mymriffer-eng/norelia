from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
]
