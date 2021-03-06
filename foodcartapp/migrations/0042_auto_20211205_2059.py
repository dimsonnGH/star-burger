# Generated by Django 3.2 on 2021-12-05 16:59

from django.db import migrations
from django.db.models import F


def set_order_item_price(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    order_items = OrderItem.objects.select_related('product').iterator()
    for order_item in order_items:
        order_item.price = order_item.product.price
        order_item.save()


def set_back_order_item_price(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    OrderItem.objects.update(price=0)


class Migration(migrations.Migration):
    dependencies = [
        ('foodcartapp', '0041_orderitem_price'),
    ]

    operations = [
        migrations.RunPython(set_order_item_price, set_back_order_item_price),
    ]
