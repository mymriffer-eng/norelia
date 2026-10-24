from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('<int:invoice_id>/download/', views.download_invoice_pdf, name='download_pdf'),
]
