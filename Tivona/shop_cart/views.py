from django.shortcuts import render
from products.models import Product, ProductImage,Variant
from django.shortcuts import render,redirect
from categories.models import Category
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from .models import Cart, CartItem,Order,OrderItem,Coupon
from user_accounts.models import Address
from products.models import Variant
from wishlist.models import Wishlist,WishlistItem
from decimal import Decimal
import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse


@never_cache
def shoping_cart(request):
    user= request.user

    if user.is_anonymous:
        return redirect('login page') 
    
    cart = Cart.objects.filter(user=user).first()

    if not cart:
        return redirect('shop')
    
    cartItems=CartItem.objects.filter(cart=cart)
    categories = Category.objects.all()
    total=0
    for item in cartItems:
        item.total_item_price= item.variant.price * item.quantity
        total += item.total_item_price
    
    context={
        'cartItems':cartItems,
        'total':total,
        'categories':categories
    }
    return render(request,'User side/shoping-cart.html',context)


@never_cache
@transaction.atomic
def add_cart(request,variant_id):
    if request.method == 'GET':
        from_wishlist=request.GET.get('from_wishlist',False)
        variant = get_object_or_404(Variant,id=variant_id)
        product=variant.product
        quantity= int(request.GET.get('quantity',1))

        if quantity>variant.stock:
            messages.error(request,"Quantity is exceeds available stock")
            return redirect('product_detail',product_slug=product.slug)

        cart ,created= Cart.objects.get_or_create(user=request.user)

        cartItem=CartItem.objects.filter(cart=cart,variant=variant).first()

        if cartItem:
            cartItem.quantity += quantity
            cartItem.save()

        else:
            cart_item,created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant =variant,
                quantity=quantity,
            )
            cart_item.save()
        
        if from_wishlist:
            user=request.user
            wishlist=Wishlist.objects.filter(user=user).first()
            wishlist_item=WishlistItem.objects.filter(wishlist=wishlist,variant=variant)
            if wishlist_item:
                wishlist_item.delete()

        
    messages.success(request,"Item added to cart successfully!")
    return redirect('product_detail',product_slug=product.slug)


@never_cache
def remove_cart(request,cartItem_id):
    user=request.user
    cart = Cart.objects.filter(user=user).first()
    cartItem = CartItem.objects.filter(cart=cart,pk=cartItem_id)
    cartItem.delete()
    messages.success(request, "Item removed from cart")
    return redirect('shoping-cart')


@never_cache
def apply_coupon(request):
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(id=coupon_id,active=True)
            if not coupon.used:
                request.session['coupon_id'] = coupon.id
                messages.success(request, "Coupon applied successfully!")
                return redirect('make_order')
            else:
               messages.success(request, "Coupon already used ") 
               return redirect('make_order')
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, "Invalid coupon code.")
            return redirect('make_order')
    return redirect('make_order')


@login_required
@never_cache
def make_order(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    cart = Cart.objects.filter(user=user).first()
    coupons = Coupon.objects.all()
    coupon_id = request.session.get('coupon_id')    

    if request.method == 'POST':
        cartItems = CartItem.objects.filter(cart=cart)

        if not cartItems.exists():
            messages.error(request, "Your cart is empty. Please add items before placing an order.")
            return redirect('shoping-cart')

        for item in cartItems:

            quantity = int(request.POST.get(f'quantity_{item.id}', item.quantity))

            if quantity>item.variant.stock:
                messages.error(request,f"{item} Quantity exceeds available stock")
                return redirect('shoping-cart')

            item.quantity = quantity
            item.save()

    cartItems = CartItem.objects.filter(cart=cart)
    Tax_Rate = Decimal(0.05)
    total=0
    for item in cartItems:
        item_price=item.variant.price * item.quantity
        total += item_price

    tax_amount = total * Tax_Rate
    total_amount = total + tax_amount

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            discount_amount = total_amount * (coupon.discount / 100)
            total_amount -= discount_amount
        except Coupon.DoesNotExist:
            pass

    tax_amount = round(tax_amount, 2)
    total_amount = round(total_amount, 2)

    context = {
        'addresses': addresses,
        'cartItems': cartItems,
        'sub_total': total,
        'total_amount': total_amount,
        'tax': tax_amount,
        'coupons': coupons,
        'coupon_amount': round(discount_amount, 2) if coupon_id else None,
    }

    return render(request, 'User side/make_order.html', context)


@never_cache
@transaction.atomic
def place_order(request):
    if request.method == 'POST':
        user = request.user
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')
        # coupon_code = request.POST.get('code')
        # new_address = Address.objects.get(id=address_id, user=user)

        try:
            new_address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            messages.error(request, "Invalid address. Please select a valid address.")
            return redirect('make_order')

        cart = Cart.objects.filter(user=user).first()
        cartItems = CartItem.objects.filter(cart=cart)

        if not cartItems.exists():
            messages.error(request, "Your cart is empty. Please add items before placing an order.")
            return redirect('make_order')
        

        Tax_Rate = Decimal(0.05)
        total = sum(item.variant.price * item.quantity for item in cartItems)
        tax_amount = total * Tax_Rate
        total_amount = total + tax_amount

        tax_amount = round(tax_amount, 2)
        total_amount = round(total_amount, 2)

        coupon_id = request.session.get('coupon_id')
        if coupon_id :
            try:
                coupon = Coupon.objects.get(id=coupon_id,active=True,used=False)
                discount_amount = total_amount * (coupon.discount / 100)
                total_amount -= discount_amount
                coupon.active = False
                coupon.used = True
                coupon.save()
                del request.session['coupon_id']
            except Coupon.DoesNotExist:
                pass

        order = Order.objects.create(
            user=user,
            order_address= new_address,
            payment_method=payment_method,
            total_amount=total_amount,
            tax_amount=tax_amount,
            status='Pending',
        )

        if coupon_id:
            coupon = Coupon.objects.get(id=coupon_id)
            try:
                order.coupon=coupon
                order.discount=discount_amount
                order.save()
            except Coupon.DoesNotExist:
                pass

        for cartItem in cartItems:
            OrderItem.objects.create(
                order=order,
                product=cartItem.product,
                variant=cartItem.variant,
                quantity=cartItem.quantity,
                price=cartItem.variant.price,
            )

            cartItem.variant.stock -= cartItem.quantity
            cartItem.variant.save()

        cartItems.delete()
        if payment_method == 'cash_on_delivery':
            # messages.success(request, "Order placed successfully!")
            return redirect('order_success', order_id=order.id)
        elif payment_method == 'razorpay':
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))
            amount = int(total_amount * 100)
            currency = 'INR'
            razorpay_order = razorpay_client.order.create({'amount': amount, 'currency': currency, 'payment_capture': '0'})
            razorpay_order_id = razorpay_order['id']
            callback_url = 'payment_success/'
            order.razorpay_order_id = razorpay_order_id
            order.save()

            context = {
                'order': order,
                'razorpay_order_id':razorpay_order_id ,
                'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                'amount': amount,
                'currency': currency,
                'callback_url': callback_url,
            }
            return render(request,'User side/make_order.html',context=context)
        
    return redirect('make_order')

@never_cache
def payment_success(request):
    print("Enter payment success")
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        print( razorpay_payment_id," ",razorpay_order_id," ",signature)

        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'signature': signature
        }

        try:
            result = razorpay_client.utility.verify_payment_signature(params_dict)
            order = get_object_or_404(Order,razorpay_order_id=razorpay_order_id) 
            amount = order.total_amount
            if result is not None:
                razorpay_client.payment.capture(razorpay_payment_id,amount)
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.status = 'Processing'
                order.save()
                return JsonResponse({'status': 'success', 'redirect_url': reverse('order_success', kwargs={'order_id': order.id})})
         
        except:
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.status = 'cancel'
            order.save()
            messages.error(request, 'Payment verification failed. Please try again.')
            return JsonResponse({'status': 'failure', 'redirect_url': reverse('make_order')})

    return JsonResponse({'redirect_url': reverse('make_order')})


@never_cache
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context={
        'order':order,
    }
    return render(request, 'User side/order_success.html',context)


