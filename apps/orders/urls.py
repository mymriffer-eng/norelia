from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('success/<str:order_number>/', views.order_success, name='order_success'),
    path('<str:order_number>/', views.order_detail, name='order_detail'),
]
