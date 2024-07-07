from django.db import models
# Create your models here.
from user_accounts.models import CustomUser,Address
from products.models import Product,Variant

class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cart of {self.user.username}'

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='product')
    variant = models.ForeignKey(Variant,on_delete=models.CASCADE,related_name='variant')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    def get_total_price(self):
        return self.product.price * self.quantity


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Order-id {self.id} by {self.user.username}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.order_items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE) 
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE) 
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.product.name} - {self.variant.color}'

    def get_cost(self):
        return self.price * self.quantity