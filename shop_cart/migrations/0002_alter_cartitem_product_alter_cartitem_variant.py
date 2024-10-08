# Generated by Django 5.0.6 on 2024-07-03 04:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_alter_variant_slug'),
        ('shop_cart', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product', to='products.product'),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variant', to='products.variant'),
        ),
    ]
