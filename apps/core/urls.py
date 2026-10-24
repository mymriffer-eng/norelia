from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
