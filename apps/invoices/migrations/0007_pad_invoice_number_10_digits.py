from django.db import migrations


def pad_numbers(apps, schema_editor):
    """NNNNNN -> 10-digit number (a number that would collide is left unchanged)"""
    Invoice = apps.get_model('invoices', 'Invoice')
    for invoice in Invoice.objects.order_by('pk'):
        number = invoice.invoice_number or ''
        if not number.isdigit() or len(number) == 10:
            continue
        new_number = f'{int(number):010d}'
        if Invoice.objects.filter(invoice_number=new_number).exclude(pk=invoice.pk).exists():
            continue
        invoice.invoice_number = new_number
        invoice.save(update_fields=['invoice_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0006_strip_invoice_year_prefix'),
    ]

    operations = [
        migrations.RunPython(pad_numbers, migrations.RunPython.noop),
    ]
