from django.shortcuts import render
from products.models import Product, ProductImage,Variant
from django.shortcuts import render,redirect
from categories.models import Category
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.contrib import messages
from .models import Cart, CartItem,Order,OrderItem
from user_accounts.models import Address
from products.models import Variant
from decimal import Decimal

@never_cache
def shoping_cart(request):
    user= request.user
    cart = Cart.objects.filter(user=user).first()
    cartItems=CartItem.objects.filter(cart=cart)
    total=0
    for item in cartItems:
        item.total_item_price=item.variant.price * item.quantity
        total += item.total_item_price
    return render(request,'User side/shoping-cart.html',{'cartItems': cartItems,'total':total})

@never_cache
def add_cart(request,variant_id):
    if request.method == 'GET':
        print("Received request to add to cart")
        variant = get_object_or_404(Variant, id=variant_id)
        quantity= int(request.GET.get('quantity',1))

        cart ,created= Cart.objects.get_or_create(user=request.user)

        cart_item,created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            quantity = quantity,
            product=variant.product,
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()
    
        product=variant.product
        variant.stock -= quantity 
        variant.save()
        product.product_count = sum(variant.stock for variant in product.variants.all())
        product.save()
        category=variant.product.category
        category.product_count = sum(product.product_count for product in category.products.all())
        category.save()

        cart_item.save()
        messages.success(request,"Item added to cart successfully!")
    return redirect('product_detail',product_slug=product.slug)


@never_cache
def remove_cart(request,cartItem_id):
    user=request.user
    if request.method=='POST':
        cart = Cart.objects.filter(user=user).first()
        cartItem = CartItem.objects.filter(cart=cart,pk=cartItem_id)
        cartItem.delete()
        return redirect('shoping-cart')
    return redirect('shoping-cart')


@login_required
@never_cache
def make_order(request):
    user=request.user
    addresses=Address.objects.filter(user=user)
    cart=Cart.objects.filter(user=user).first()
    
    cartItems=CartItem.objects.filter(cart=cart)

    if not cartItems.exists():
        messages.error(request, "Your cart is empty. Please add items before placing an order.")
        return redirect('shoping-cart')
    
    Tax_Rate = Decimal(0.05)
    total=0
    for item in cartItems:
        item_price=item.variant.price * item.quantity
        total +=item_price
    tax_amount = total * Tax_Rate
    total_amount = total + tax_amount

    tax_amount = round(tax_amount, 2)
    total_amount = round(total_amount, 2)

    context={
        'addresses':addresses,
        'cartItems':cartItems,
        'sub_total':total,
        'total_amount':total_amount,
        'tax':tax_amount
    }
    return render(request,'User side/make_order.html',context)

@never_cache
def place_order(request):
    if request.method=='POST':
        user = request.user
        address_id = request.POST.get('address_id')
        payment_method=request.POST.get('payment_method')
        cart=Cart.objects.filter(user=user).first()
        cartItems=CartItem.objects.filter(cart=cart)

        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            messages.error(request, "Invalid address. Please select a valid address.")
            return redirect('make_order')

        Tax_Rate = Decimal(0.05)
        total = sum(item.variant.price * item.quantity for item in cartItems)
        tax_amount = total * Tax_Rate
        total_amount = total + tax_amount

        tax_amount = round(tax_amount, 2)
        total_amount = round(total_amount, 2)

        order = Order.objects.create(
            user=user,
            address=address,
            payment_method=payment_method,
            total_amount=total_amount,
            status='Pending',
        )

        for cartItem in cartItems:
            OrderItem.objects.create(
                order=order,
                product=cartItem.product,
                variant=cartItem.variant,
                quantity=cartItem.quantity,
                price=cartItem.variant.price,
            )
        
        cartItems.delete()
        messages.success(request, "Order placed successfully!")
        return redirect('order_success',order_id=order.id)
    return redirect('shoping-cart')

@never_cache
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'User side/order_success.html', {'order': order})
