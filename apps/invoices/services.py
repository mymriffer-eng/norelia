from io import BytesIO
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .models import Invoice
from apps.core.models import SiteSettings


class InvoiceService:
    """Service for invoice operations"""
    
    def create_invoice_for_order(self, order):
        """Create invoice from order"""
        from django.utils import timezone
        
        # Check if invoice already exists
        if hasattr(order, 'invoice'):
            return order.invoice
        
        # Generate invoice number
        invoice_number = Invoice.generate_invoice_number()
        
        # Create invoice
        invoice = Invoice.objects.create(
            order=order,
            invoice_number=invoice_number,
            invoice_date=timezone.now().date(),
            customer_name=order.get_full_name(),
            customer_email=order.email,
            customer_phone=order.phone,
            customer_address=f'{order.city}, {order.address}',
            subtotal=order.subtotal,
            shipping_cost=order.shipping_cost,
            total=order.total,
            notes=order.notes
        )
        
        return invoice
    
    def generate_pdf(self, invoice):
        """Generate PDF for invoice using ReportLab"""
        buffer = BytesIO()
        
        # Register fonts with Cyrillic support
        try:
            # Try to register Windows Arial fonts (support Cyrillic)
            pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
            font_name = 'Arial'
            font_bold = 'Arial-Bold'
        except:
            # Fallback to Helvetica if Arial is not found
            font_name = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Container for elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Update default styles to use Cyrillic-compatible font
        for style in styles.byName.values():
            style.fontName = font_name
            if 'Bold' in style.fontName or style.fontName.endswith('B'):
                style.fontName = font_bold
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            fontName=font_bold,
            textColor=colors.HexColor('#C59D5F'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Get site settings
        try:
            site_settings = SiteSettings.objects.first()
            company_name = site_settings.company_name or 'Norelia'
            company_vat = site_settings.company_vat or ''
            company_address = site_settings.company_address or ''
        except:
            company_name = 'Norelia'
            company_vat = ''
            company_address = ''
        
        # Title
        elements.append(Paragraph("ФАКТУРА", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Company and invoice info
        order_number = invoice.order.order_number if invoice.order else '-'
        info_data = [
            ['Издател:', company_name, 'Фактура №:', invoice.invoice_number],
            ['ЕИК:', company_vat, 'Дата:', invoice.invoice_date.strftime('%d.%m.%Y')],
            ['Адрес:', company_address, 'Поръчка №:', order_number],
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), font_bold),
            ('FONTNAME', (2, 0), (2, -1), font_bold),
            ('FONTNAME', (1, 0), (1, -1), font_name),
            ('FONTNAME', (3, 0), (3, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 1*cm))
        
        # Customer info
        if invoice.is_company:
            elements.append(Paragraph("<b>Фирмени данни:</b>", styles['Heading3']))
            customer_data = [
                ['Фирма:', invoice.customer_name],
                ['ЕИК/Булстат:', invoice.company_vat or '-'],
                ['ДДС номер:', invoice.company_vat_number or '-'],
                ['МОЛ:', invoice.company_mol or '-'],
                ['Телефон:', invoice.customer_phone],
                ['Имейл:', invoice.customer_email or '-'],
                ['Адрес:', invoice.customer_address],
            ]
        else:
            elements.append(Paragraph("<b>Клиент:</b>", styles['Heading3']))
            customer_data = [
                ['Име:', invoice.customer_name],
                ['Телефон:', invoice.customer_phone],
                ['Имейл:', invoice.customer_email or '-'],
                ['Адрес:', invoice.customer_address],
            ]
        
        customer_table = Table(customer_data, colWidths=[3*cm, 14*cm])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), font_bold),
            ('FONTNAME', (1, 0), (1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 1*cm))
        
        # Items table - check if invoice has items (manual or from order)
        invoice_items = invoice.items.all()
        
        if invoice_items.exists():
            elements.append(Paragraph("<b>Поръчани артикули:</b>", styles['Heading3']))
            elements.append(Spacer(1, 0.3*cm))
            
            # Table header
            items_data = [['№', 'Артикул', 'SKU', 'Кол.', 'Цена (лв.)', 'Сума (лв.)']]
            
            # Add items from invoice items
            for idx, item in enumerate(invoice_items, 1):
                items_data.append([
                    str(idx),
                    item.product_name,
                    item.product_sku or '-',
                    str(item.quantity),
                    f'{item.price:.2f}',
                    f'{item.subtotal:.2f}'
                ])
            
            # Add totals with discount if applicable
            items_data.append(['', '', '', '', 'Междинна сума:', f'{invoice.subtotal:.2f}'])
            
            if invoice.trade_discount_percent > 0:
                items_data.append(['', '', '', '', f'Търговска отстъпка ({invoice.trade_discount_percent}%):', f'-{invoice.trade_discount_amount:.2f}'])
                items_data.append(['', '', '', '', 'След отстъпка:', f'{invoice.subtotal_after_discount:.2f}'])
            
            items_data.append(['', '', '', '', 'Доставка:', f'{invoice.shipping_cost:.2f}'])
            items_data.append(['', '', '', '', 'ОБЩО:', f'{invoice.total:.2f}'])
            
            items_table = Table(items_data, colWidths=[1*cm, 7*cm, 3*cm, 1.5*cm, 2.5*cm, 2*cm])
            items_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C59D5F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), font_bold),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Body
                ('FONTNAME', (0, 1), (-1, -4), font_name),
                ('FONTSIZE', (0, 1), (-1, -4), 9),
                ('ALIGN', (3, 1), (3, -4), 'CENTER'),
                ('ALIGN', (4, 1), (-1, -4), 'RIGHT'),
                
                # Totals
                ('FONTNAME', (4, -3), (-1, -1), font_bold),
                ('ALIGN', (4, -3), (-1, -1), 'RIGHT'),
                
                # Grand total
                ('FONTSIZE', (4, -1), (-1, -1), 12),
                ('BACKGROUND', (4, -1), (-1, -1), colors.HexColor('#F5F5F5')),
                
                # Grid
                ('GRID', (0, 0), (-1, -4), 1, colors.grey),
                ('LINEABOVE', (4, -3), (-1, -1), 1, colors.grey),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 1*cm))
        else:
            # For manual invoices without order, just show the total
            elements.append(Paragraph("<b>Сума за плащане:</b>", styles['Heading3']))
            elements.append(Spacer(1, 0.3*cm))
            
            total_data = [
                ['Междинна сума:', f'{invoice.subtotal:.2f} лв.'],
                ['Доставка:', f'{invoice.shipping_cost:.2f} лв.'],
                ['ОБЩО:', f'{invoice.total:.2f} лв.'],
            ]
            
            total_table = Table(total_data, colWidths=[14*cm, 3*cm])
            total_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_bold),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, -1), (-1, -1), 14),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ]))
            elements.append(total_table)
            elements.append(Spacer(1, 1*cm))

        
        # Payment info
        elements.append(Paragraph("<b>Начин на плащане:</b> Наложен платеж", styles['Normal']))
        
        # Notes
        if invoice.notes:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(f"<b>Бележки:</b> {invoice.notes}", styles['Normal']))
        
        elements.append(Spacer(1, 2*cm))
        
        # Footer
        footer_text = "Благодарим Ви за покупката! / Thank you for your purchase!"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName=font_name,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        elements.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(elements)
        
        buffer.seek(0)
        return buffer
