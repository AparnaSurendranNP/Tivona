# Generated by Django 5.0.6 on 2024-06-04 04:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_accounts', '0005_remove_customuser_otp'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='phone',
            field=models.CharField(max_length=12, null=True, unique=True),
        ),
    ]
