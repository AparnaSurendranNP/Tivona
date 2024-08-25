from django.db import models

# Create your models here.

from user_accounts.models import CustomUser
from products.models import Product,Variant

class Wishlist(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Wishlist of {self.user.username}'

    def get_total_items(self):
        return self.items.count()

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='wishlist_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='wishlist_product')
    variant = models.ForeignKey(Variant,on_delete=models.CASCADE,related_name='wishlist_variant')

    def __str__(self):
        return f'Wishlist of {self.product}'