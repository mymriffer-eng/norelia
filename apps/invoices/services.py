import os
import re
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .models import Invoice, InvoiceItem, split_vat, get_vat_rate
from apps.core.models import SiteSettings


def _clean(value):
    """Single-line text: line breaks/control characters render as boxes in PDF tables"""
    text = re.sub(r'\s*[\r\n]+\s*', ', ', str(value or ''))
    text = ''.join(ch for ch in text if ch.isprintable())
    return text.strip(' ,')


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
        
        # Copy ordered products into invoice lines (prices are VAT-inclusive)
        InvoiceItem.objects.bulk_create([
            InvoiceItem(
                invoice=invoice,
                product_sku=item.product_sku,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
                subtotal=item.subtotal,
            )
            for item in order.items.all()
        ])
        
        return invoice
    
    @staticmethod
    def get_lines(invoice):
        """Invoice lines; falls back to the order items for older invoices without lines"""
        lines = [
            {
                'sku': item.product_sku,
                'name': item.product_name,
                'quantity': item.quantity,
                'price': item.price,
                'subtotal': item.subtotal,
            }
            for item in invoice.items.all()
        ]
        if not lines and invoice.order:
            lines = [
                {
                    'sku': item.product_sku,
                    'name': item.product_name,
                    'quantity': item.quantity,
                    'price': item.price,
                    'subtotal': item.subtotal,
                }
                for item in invoice.order.items.all()
            ]
        return lines
    
    def generate_pdf(self, invoice):
        """Generate PDF for invoice using ReportLab"""
        buffer = BytesIO()
        
        # Register fonts with Cyrillic support
        # Prefer Windows Arial when available; otherwise fall back to common Linux fonts
        # that include Cyrillic glyphs. Helvetica does not support Bulgarian/Cyrillic text.
        bundled_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        font_candidates = {
            'DejaVuSans': [
                os.path.join(bundled_dir, 'DejaVuSans.ttf'),
            ],
            'DejaVuSans-Bold': [
                os.path.join(bundled_dir, 'DejaVuSans-Bold.ttf'),
            ],
            'Arial': [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf',
            ],
            'Arial-Bold': [
                'C:/Windows/Fonts/arialbd.ttf',
                'C:/Windows/Fonts/arialbd.ttf',
                'C:/Windows/Fonts/calibrib.ttf',
            ],
        }

        font_name = 'Helvetica'
        font_bold = 'Helvetica-Bold'

        for font_key, paths in font_candidates.items():
            for path in paths:
                if not path or not os.path.exists(path):
                    continue
                try:
                    pdfmetrics.registerFont(TTFont(font_key, path))
                    if font_key == 'Arial' or font_key == 'DejaVuSans':
                        font_name = font_key
                    if font_key == 'Arial-Bold' or font_key == 'DejaVuSans-Bold':
                        font_bold = font_key
                    break
                except Exception:
                    continue
            if font_name != 'Helvetica' and font_bold != 'Helvetica-Bold':
                break
        
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
        number_data = [
            ['Фактура №:', invoice.invoice_number],
            ['Дата:', invoice.invoice_date.strftime('%d.%m.%Y')],
            ['Поръчка №:', order_number],
        ]
        number_table = Table(number_data, colWidths=[3*cm, 6*cm], hAlign='LEFT')
        number_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), font_bold),
            ('FONTNAME', (1, 0), (1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(number_table)
        elements.append(Spacer(1, 0.6*cm))
        
        info_data = [
            ['Издател:', _clean(company_name)],
            ['ЕИК:', _clean(company_vat)],
            ['Адрес:', _clean(company_address)],
        ]
        
        value_style = ParagraphStyle(
            'InfoValue', parent=styles['Normal'], fontName=font_name, fontSize=10, leading=12
        )
        info_data = [[k, Paragraph(escape(v), value_style)] for k, v in info_data]
        
        info_table = Table(info_data, colWidths=[3*cm, 14*cm], hAlign='LEFT')
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), font_bold),
            ('FONTNAME', (1, 0), (1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 1*cm))
        
        # Customer info
        if invoice.is_company:
            elements.append(Paragraph("<b>Фирмени данни:</b>", styles['Heading3']))
            customer_data = [
                ['Фирма:', _clean(invoice.customer_name)],
                ['ЕИК/Булстат:', _clean(invoice.company_vat) or '-'],
                ['ДДС номер:', _clean(invoice.company_vat_number) or '-'],
                ['МОЛ:', _clean(invoice.company_mol) or '-'],
                ['Телефон:', _clean(invoice.customer_phone)],
                ['Имейл:', _clean(invoice.customer_email) or '-'],
                ['Адрес:', _clean(invoice.customer_address)],
            ]
        else:
            elements.append(Paragraph("<b>Клиент:</b>", styles['Heading3']))
            customer_data = [
                ['Име:', _clean(invoice.customer_name)],
                ['Телефон:', _clean(invoice.customer_phone)],
                ['Имейл:', _clean(invoice.customer_email) or '-'],
                ['Адрес:', _clean(invoice.customer_address)],
            ]
        
        customer_data = [[k, Paragraph(escape(v), value_style)] for k, v in customer_data]
        customer_table = Table(customer_data, colWidths=[3*cm, 14*cm], hAlign='LEFT')
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), font_bold),
            ('FONTNAME', (1, 0), (1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 1*cm))
        
        # Items table (prices shown without and with VAT)
        lines = self.get_lines(invoice)
        vat_percent = (get_vat_rate() * 100).quantize(Decimal('0.01')).normalize()
        vat_percent_text = f'{vat_percent:f}'
        
        if lines:
            elements.append(Paragraph("<b>Артикули:</b>", styles['Heading3']))
            elements.append(Spacer(1, 0.3*cm))
            
            cell_style = ParagraphStyle(
                'ItemCell',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=8,
                leading=10,
            )
            head_style = ParagraphStyle(
                'ItemHead',
                parent=cell_style,
                fontName=font_bold,
                textColor=colors.white,
                alignment=TA_CENTER,
            )
            
            items_data = [[
                Paragraph('№', head_style),
                Paragraph('Код', head_style),
                Paragraph('Наименование', head_style),
                Paragraph('Кол.', head_style),
                Paragraph('Ед. цена без ДДС', head_style),
                Paragraph('Ед. цена с ДДС', head_style),
                Paragraph('Сума без ДДС', head_style),
                Paragraph('Сума с ДДС', head_style),
            ]]
            
            for idx, line in enumerate(lines, 1):
                unit_net, _ = split_vat(line['price'])
                line_net, _ = split_vat(line['subtotal'])
                items_data.append([
                    str(idx),
                    line['sku'] or '-',
                    Paragraph(escape(line['name']), cell_style),
                    str(line['quantity']),
                    f'{unit_net:.2f}',
                    f'{line["price"]:.2f}',
                    f'{line_net:.2f}',
                    f'{line["subtotal"]:.2f}',
                ])
            
            items_table = Table(
                items_data,
                colWidths=[0.8*cm, 2.3*cm, 5.1*cm, 1.2*cm, 1.9*cm, 1.9*cm, 1.9*cm, 1.9*cm],
                repeatRows=1,
            )
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C59D5F')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 1), (1, -1), 'CENTER'),
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),
                ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 0.5*cm))
        
        # Totals
        total_net, total_vat = split_vat(invoice.total)
        totals = []  # (label, value, style)
        
        if invoice.trade_discount_percent > 0:
            totals.append(('Сума с ДДС:', f'{invoice.subtotal:.2f} €', 'normal'))
            totals.append((f'Търговска отстъпка ({invoice.trade_discount_percent}%):', f'-{invoice.trade_discount_amount:.2f} €', 'normal'))
            totals.append(('Сума след отстъпка:', f'{invoice.subtotal_after_discount:.2f} €', 'normal'))
        
        if invoice.shipping_cost and invoice.shipping_cost > 0:
            totals.append(('Доставка:', f'{invoice.shipping_cost:.2f} €', 'normal'))
        else:
            totals.append(('Доставка: според тарифата на куриера', '', 'normal'))
        
        totals.append(('Данъчна основа (без ДДС):', f'{total_net:.2f} €', 'bold'))
        totals.append((f'ДДС {vat_percent_text}%:', f'{total_vat:.2f} €', 'bold'))
        totals.append(('ОБЩО за плащане (с ДДС):', f'{invoice.total:.2f} €', 'grand'))
        
        total_table = Table([[label, value] for label, value, _ in totals], colWidths=[13*cm, 4*cm])
        total_style = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        for row, (_, _, kind) in enumerate(totals):
            if kind in ('bold', 'grand'):
                total_style.append(('FONTNAME', (0, row), (-1, row), font_bold))
            if kind == 'grand':
                total_style.append(('FONTSIZE', (0, row), (-1, row), 12))
                total_style.append(('BACKGROUND', (0, row), (-1, row), colors.HexColor('#F5F5F5')))
                total_style.append(('LINEABOVE', (0, row), (-1, row), 1, colors.black))
        total_style.append(('BOX', (0, 0), (-1, -1), 1.5, colors.black))
        total_table.setStyle(TableStyle(total_style))
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
