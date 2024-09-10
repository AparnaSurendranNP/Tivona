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
        if self.variant.discount_amount:
            price = self.variant.discount_amount
        else:
            price = self.variant.price
        return price * self.quantity
    
    

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    min_amount = models.PositiveIntegerField(default=100)
    max_amount = models.PositiveIntegerField(default=500)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=False)
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    razorpay_order_id = models.CharField(max_length=20,blank=True,null=True)
    address = models.ForeignKey(Address,on_delete=models.CASCADE, null=True, blank=True)
    order_address = models.CharField(max_length=100, null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount=models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_listed = models.BooleanField(default=True)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)
    refunded_to_wallet = models.BooleanField(default=False)

    def __str__(self):
        return f'Order-id {self.id} by {self.user.username}'

    def get_total_cost(self):
        total_cost = sum(item.get_cost() for item in self.order_items.all())
        if self.coupon:
            total_cost -= self.discount
        return total_cost
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE) 
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE) 
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_listed = models.BooleanField(default=True)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.product.name} - {self.variant.color}'

    def get_cost(self):
        return self.price * self.quantity