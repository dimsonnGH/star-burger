# Generated by Django 3.2 on 2021-12-24 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0045_alter_order_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(blank=True, choices=[('CARD', 'Картой'), ('CASH', 'Наличными')], max_length=15, verbose_name='Способ оплаты'),
        ),
    ]
