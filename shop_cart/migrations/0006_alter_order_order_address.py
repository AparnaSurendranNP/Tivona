# Generated by Django 5.0.6 on 2024-07-10 10:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_cart', '0005_rename_address_order_order_address'),
        ('user_accounts', '0015_rename_user_address_address_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='user_accounts.address'),
        ),
    ]
