# Generated by Django 5.0.6 on 2024-07-21 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_cart', '0010_coupon_order_discount_order_coupon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
