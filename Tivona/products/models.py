from django.db import models
# Create your models here.
from django.db import models
from categories.models import Category
from image_cropping import ImageRatioField
from django.utils.text import slugify

class Product(models.Model):
    name = models.CharField(max_length=20)
    image = models.ImageField(upload_to='product_image/', blank=False, null=False)
    cropping = ImageRatioField('image', '430x360')
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    is_listed = models.BooleanField(default=True)
    offer_applied =models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Variant(models.Model):
    color = models.CharField(max_length=100,default=None)
    price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=1)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_listed = models.BooleanField(default=True)
    slug = models.SlugField(unique=False,blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.product.name}-{self.color}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Variant: {self.color} for {self.product.name}"


class ProductImage(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='images',null=False)
    image = models.ImageField(upload_to='product_images/', blank=False, null=False)
    cropping = ImageRatioField('image', '1x1')

    def __str__(self):
        return f"Image for {self.variant.product.name} - {self.variant.color}"
