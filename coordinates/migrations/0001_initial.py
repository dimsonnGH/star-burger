# Generated by Django 3.2 on 2022-01-16 13:32

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=500, unique=True, verbose_name='адрес')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='долгота')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='широта')),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, verbose_name='дата обновления')),
            ],
            options={
                'verbose_name': 'место',
                'verbose_name_plural': 'места',
            },
        ),
    ]
