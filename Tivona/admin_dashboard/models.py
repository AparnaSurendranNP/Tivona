from django.db import models
from categories.models import Category
from products.models import Product,Variant
from datetime import timezone
# Create your models here.

class CategoryOffer(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name='offer')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category.name} - {self.discount_percentage}%"
    

class ProductOffer(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='offer')
    variant = models.OneToOneField(Variant, on_delete=models.CASCADE, related_name='variant_offer')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} - {self.discount_percentage}%"
   