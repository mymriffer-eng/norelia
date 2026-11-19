from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('cookies/', views.cookie_policy, name='cookies'),
    path('terms/', views.terms, name='terms'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/confirm/<str:token>/', views.newsletter_confirm, name='newsletter_confirm'),
    path('newsletter/unsubscribe/<str:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
