# Generated by Django 5.0.6 on 2024-06-26 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_remove_product_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_count',
            field=models.IntegerField(default=0),
        ),
    ]
