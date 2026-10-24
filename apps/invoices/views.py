from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Invoice
from .services import InvoiceService


@staff_member_required
def download_invoice_pdf(request, invoice_id):
    """Download invoice as PDF"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice_service = InvoiceService()
    
    pdf_buffer = invoice_service.generate_pdf(invoice)
    
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice-{invoice.invoice_number}.pdf"'
    
    return response
