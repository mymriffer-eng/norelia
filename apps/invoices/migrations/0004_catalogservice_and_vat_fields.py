from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0003_alter_invoice_options_invoiceitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='CatalogService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Код')),
                ('name', models.CharField(max_length=200, verbose_name='Наименование')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена с ДДС (€)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
            ],
            options={
                'verbose_name': 'Услуга',
                'verbose_name_plural': 'Услуги',
                'ordering': ['code'],
            },
        ),
        migrations.AlterField(
            model_name='invoice',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Междинна сума (с ДДС)'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Обща сума (с ДДС)'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='trade_discount_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Сума отстъпка (€)'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='product_sku',
            field=models.CharField(blank=True, help_text='Код на продукт (SKU) или услуга - попълва наименованието и цената автоматично', max_length=50, verbose_name='Код'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='product_name',
            field=models.CharField(blank=True, max_length=200, verbose_name='Наименование'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Ед. цена с ДДС (€)'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=10, verbose_name='Сума с ДДС (€)'),
        ),
    ]
