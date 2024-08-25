from django.shortcuts import render
from django.shortcuts import render,redirect
from django.contrib.auth import login
from categories.models import Category
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from shop_cart.models import Cart, CartItem,Order,OrderItem,Coupon
from user_accounts.models import Address
from products.models import Variant
from wishlist.models import Wishlist,WishlistItem
from user_profile.models import Wallet,WalletTransaction
from admin_dashboard.models import ProductOffer
from products.models import Product
from decimal import Decimal
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.middleware.csrf import get_token
from django.http import JsonResponse
import json
from django.http import HttpResponse
import pdfkit
from django.template.loader import render_to_string

@never_cache
@login_required
def shoping_cart(request):
    user= request.user

    if user.is_anonymous:
        return redirect('login page') 
    
    cart = Cart.objects.filter(user=user).first()

    if not cart:
        return redirect('shop')
    
    cartItems = CartItem.objects.filter(cart=cart)
    categories = Category.objects.all()
    total=0

    for item in cartItems:
        product= item.product
        variant = item.variant

        item.discounted_price = variant.price

        if product.offer_applied:
            offer = ProductOffer.objects.filter(product=product).first()
            if offer and offer.is_active and offer.variant == variant:
                item.discounted_price = variant.discounted_price or variant.price

        item.total_item_price = item.discounted_price * item.quantity
        total += item.total_item_price
    
    context = {
        'cartItems':cartItems,
        'total':total,
        'categories':categories
    }
    return render(request,'User side/shoping-cart.html',context)


@never_cache
@transaction.atomic
@login_required
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
@login_required
def remove_cart(request,cartItem_id):
    user=request.user
    cart = Cart.objects.filter(user=user).first()
    cartItem = CartItem.objects.filter(cart=cart,pk=cartItem_id)
    cartItem.delete()
    messages.success(request, "Item removed from cart")
    return redirect('shoping-cart')

@never_cache
@login_required
def apply_coupon(request):
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(id=coupon_id,active=True)
            request.session['coupon_id'] = coupon.id
            messages.success(request, "Coupon applied successfully!")
            return redirect('make_order')
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, "Invalid coupon code.")
            return redirect('make_order')
    return redirect('make_order')



@never_cache
@login_required
def remove_coupon(request):
    try:
        if 'coupon_id'in request.session:
            del request.session['coupon_id']
            messages.error(request, 'Removed coupon successfully')
            return redirect('make_order')
        else:
            messages.error(request, "Coupon does not exit")
            return redirect('make_order')
    except Coupon.DoesNotExist:
        request.session['coupon_id'] = None
        messages.error(request, "Invalid coupon code.")
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
    Del_Charge = Decimal(50)
    total = Decimal(0)
    discount_amount = Decimal(0)

    for item in cartItems:
        product= item.product
        variant = item.variant

        item.discounted_price = variant.price

        if product.offer_applied:
            offer = ProductOffer.objects.filter(product=product).first()
            if offer and offer.is_active and offer.variant == variant:
                item.discounted_price = variant.discounted_price or variant.price

        item.total_item_price = item.discounted_price * item.quantity
        total += item.total_item_price

    tax_amount = total * Tax_Rate
    total_amount = total + tax_amount + Del_Charge

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            discount_amount = total_amount * (coupon.discount / 100)
            total_amount = total_amount - discount_amount
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid address. Please select a valid address.")
            return redirect('make_order')
        
    tax_amount = round(tax_amount, 2)
    total_amount = round(total_amount, 2)
    discount_amount = round(discount_amount, 2)

    context = {
        'addresses': addresses,
        'cartItems': cartItems,
        'sub_total': total,
        'total_amount': total_amount,
        'tax': tax_amount,
        'del_charge':Del_Charge,
        'coupons': coupons,
        'coupon_amount': discount_amount if coupon_id else None,
    }

    return render(request, 'User side/make_order.html', context)

@never_cache
@login_required
def place_order(request):
    if request.method == 'POST':
        user = request.user
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')
        
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
        total = Decimal(0)
        Del_Charge = Decimal(50)
        discount_amount = Decimal(0)

        for item in cartItems:
            product= item.product
            variant = item.variant

            item.discounted_price = variant.price

            if product.offer_applied:
                offer = ProductOffer.objects.filter(product=product).first()
                if offer and offer.is_active and offer.variant == variant:
                    item.discounted_price = variant.discounted_price or variant.price

            item.total_item_price = item.discounted_price * item.quantity
            total += item.total_item_price
            
        tax_amount = total * Tax_Rate
        total_amount = total + tax_amount + Del_Charge

        tax_amount = round(tax_amount, 2)
        total_amount = round(total_amount, 2)

        coupon_id = request.session.get('coupon_id')

        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, active=True)
                discount_amount = round(total_amount * (coupon.discount / 100), 2)
                total_amount -= discount_amount
            except Coupon.DoesNotExist:
                del request.session['coupon_id']
                messages.error(request, 'Invalid coupon.')
                return redirect('make_order')

        if payment_method == 'cash_on_delivery' or payment_method == 'wallet':

            if total_amount > 1000 and payment_method == 'cash_on_delivery' :
                messages.error(request,"Order above ₹1000 cannot be placed using Cash On Delivery.")
                return redirect('make_order')

            if payment_method == 'wallet':

                wallet, created = Wallet.objects.get_or_create(user=user)

                if wallet.balance == 0 or wallet.balance < total_amount:
                    messages.error(request,"Insufficient wallet amount")
                    return redirect('make_order')

            order = Order.objects.create(
                user=user,
                order_address=str(new_address),
                total_amount=total_amount,
                tax_amount=tax_amount,
                discount=discount_amount,
                status='Processing',
                payment_method='Wallet' if payment_method == 'wallet' else 'Cash on delivery',
            )

            if payment_method == 'wallet':
                
                if not isinstance(wallet.balance, Decimal):
                    wallet.balance = Decimal(wallet.balance)

                wallet.balance -= Decimal(order.total_amount)
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=order.total_amount,
                    transaction_type='debited'
                )

            if coupon_id:
                order.coupon = coupon
                coupon.used = True
                coupon.save()
                del request.session['coupon_id']

            for cartItem in cartItems:
                OrderItem.objects.create(
                    order=order,
                    product=cartItem.product,
                    variant=cartItem.variant,
                    quantity=cartItem.quantity,
                    price=cartItem.discounted_price,
                )
                cartItem.variant.stock -= cartItem.quantity
                cartItem.variant.save()

            cartItems.delete()

            messages.success(request, "Your order has been placed successfully.")
            return redirect('order_success', order_id=order.id)


        elif payment_method == 'razorpay':
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_SECRET_KEY))
            amount = int(total_amount * 100)
            currency = 'INR'
            razorpay_order = razorpay_client.order.create({'amount': amount, 'currency': currency, 'payment_capture': '0'})
            razorpay_order_id = razorpay_order['id']

            context = {
                'address_id':address_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                'amount': amount,
                'currency': currency,
                'csrf_token': get_token(request),
                'discount_amount': discount_amount,
            }
            return render(request, 'User side/make_order.html', context=context)

    return redirect('make_order')


@login_required
@never_cache
@csrf_exempt
def online_payment_success(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)

            razorpay_payment_id = data.get('razorpay_payment_id', '')
            razorpay_order_id = data.get('razorpay_order_id', '')
            razorpay_signature = data.get('razorpay_signature', '')
            amount = data.get('amount')
            address_id = data.get('address_id')
            discount_amount = data.get('discount_amount', '0')

            # Ensure user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'message': 'User not authenticated'})

            user = request.user

            # Razorpay client setup
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

            # Prepare the signature verification parameters
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            }

            # Verify the payment signature
            razorpay_client.utility.verify_payment_signature(params_dict)
            # Payment verified successfully, proceed to create the order
            new_address = get_object_or_404(Address, id=address_id, user=user)
            cart = get_object_or_404(Cart, user=user)
            cartItems = CartItem.objects.filter(cart=cart)

            total_amount = Decimal(amount) / 100  # Convert back from paise to INR
            tax_amount = round(total_amount * Decimal(0.05) / Decimal(1.05), 2)  # Reverse calculate tax from total
            
            # Create the order
            order = Order.objects.create(
                user=user,
                order_address=str(new_address),
                payment_method='Razorpay',
                total_amount=total_amount,
                tax_amount=tax_amount,
                discount=Decimal(discount_amount),
                status='Processing',
                razorpay_order_id=razorpay_order_id,
            )
            

            # Create order items and update stock
            for cartItem in cartItems:
                product = cartItem.product
                variant = cartItem.variant

                cartItem.discounted_price = variant.price

                if product.offer_applied:
                    offer = ProductOffer.objects.filter(product=product).first()
                    if offer and offer.is_active and offer.variant == variant:
                        cartItem.discounted_price = variant.discounted_price or variant.price

                OrderItem.objects.create(
                    order=order,
                    product=cartItem.product,
                    variant=cartItem.variant,
                    quantity=cartItem.quantity,
                    price=cartItem.discounted_price,
                )
                cartItem.variant.stock -= cartItem.quantity
                cartItem.variant.save()

            # Delete cart items after order is placed
            cartItems.delete()

            # Clear the coupon session if used
            if 'coupon_id' in request.session:
                coupon_id = request.session['coupon_id']
                coupon = Coupon.objects.filter(id=coupon_id, active=True).first()
                order.coupon = coupon
                coupon.used = True
                coupon.save()
                del request.session['coupon_id']
            order.save()

            # Respond with success and redirect URL
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('order_success', kwargs={'order_id': order.id}),
            })

        except razorpay.errors.SignatureVerificationError as e:
            return JsonResponse({'success': False, 'message': f"Payment verification failed: {str(e)}"})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"An error occurred: {str(e)}"})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})



@never_cache
@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context={
        'order':order,
    }
    return render(request, 'User side/order_success.html',context)

@login_required
@never_cache
def download_invoice_pdf(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    context = {
        'order': order,
    }

    # Render HTML content from template with context data
    html = render_to_string('User side/invoice_pdf.html', context)
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

    # Generate PDF from HTML using pdfkit
    pdf = pdfkit.from_string(html, False, configuration=config)

    # Create HTTP response with the PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    return response

@login_required
@never_cache
def request_refund(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Delivered' or order.payment_method == 'Razorpay' or order.payment_method == 'Wallet':
        order.refund_requested = True
        order.status = 'Refund processed'
        order.save()
        messages.success(request, "Refund request submitted successfully.")
    else:
        messages.error(request, "Order cannot be refunded.")
    return redirect('order_detail',order_id=order_id)

