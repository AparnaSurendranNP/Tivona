# Generated by Django 5.0.6 on 2024-09-10 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_cart', '0021_orderitem_is_listed_orderitem_refund_granted_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
