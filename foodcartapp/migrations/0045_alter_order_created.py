# Generated by Django 3.2 on 2021-12-19 15:28

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0044_auto_20211219_1705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='created',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='дата создания'),
        ),
    ]
