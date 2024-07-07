from django.contrib import admin

# Register your models here.
from .models import Product,Variant,ProductImage

admin.site.register(Product)
admin.site.register(Variant)
admin.site.register(ProductImage)