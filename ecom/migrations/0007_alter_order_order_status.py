# Generated by Django 4.2.6 on 2024-02-22 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0006_order_order_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('FAILED', 'Failed')], default='PENDING', max_length=50),
        ),
    ]
