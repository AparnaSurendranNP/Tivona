# Generated by Django 5.0.6 on 2024-06-16 14:56

import image_cropping.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0007_remove_categories_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='categories',
            name='cropping',
            field=image_cropping.fields.ImageRatioField('image', '430x360', adapt_rotation=False, allow_fullsize=False, free_crop=False, help_text=None, hide_image_field=False, size_warning=False, verbose_name='cropping'),
        ),
        migrations.AddField(
            model_name='categories',
            name='slug',
            field=models.SlugField(blank=True, unique=True),
        ),
    ]
