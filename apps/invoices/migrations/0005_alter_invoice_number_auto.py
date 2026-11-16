from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0004_catalogservice_and_vat_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='invoice_number',
            field=models.CharField(blank=True, editable=False, help_text='Задава се автоматично', max_length=50, unique=True, verbose_name='Номер на фактура'),
        ),
    ]
