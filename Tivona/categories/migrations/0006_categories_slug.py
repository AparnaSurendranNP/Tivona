# Generated by Django 5.0.6 on 2024-06-15 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0005_alter_categories_is_listed'),
    ]

    operations = [
        migrations.AddField(
            model_name='categories',
            name='slug',
            field=models.SlugField(blank=True, unique=True),
        ),
    ]
