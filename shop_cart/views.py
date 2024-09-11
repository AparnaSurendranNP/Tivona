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
from products.utils import colors
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
from django.http import Http404


@never_cache
@login_required
def shoping_cart(request):
    try:
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
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('home page')


@never_cache
@transaction.atomic
@login_required
def add_cart(request,variant_id):
    try:
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
    except Http404:
        messages.error(request,"Variant not Found")
        return redirect('home page')
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('home page')
    


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
    try:
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
                discount_amount = round(total_amount * (coupon.discount / 100), 2)
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
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('shoping-cart')

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
            razorpay_order = razorpay_client.order.create({'amount': amount, 'currency': currency, 'payment_capture': 1})
            razorpay_order_id = razorpay_order['id']

            order = Order.objects.create(
                user=user,
                order_address=str(new_address),
                payment_method='Razorpay',
                total_amount=total_amount,
                tax_amount=tax_amount,
                discount=Decimal(discount_amount),
                razorpay_order_id=razorpay_order_id,
            )
            print("Order created:", order)

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

            cartItems.delete()

            if 'coupon_id' in request.session:
                coupon_id = request.session['coupon_id']
                coupon = Coupon.objects.filter(id=coupon_id, active=True).first()
                if coupon:
                    order.coupon = coupon
                    coupon.used = True
                    coupon.save()
                    del request.session['coupon_id']

            order.save()

            context = {
                'address_id':address_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                'order':order,
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
            data = json.loads(request.body)
            print("Incoming data:", data)

            razorpay_payment_id = data.get('razorpay_payment_id', '')
            razorpay_order_id = data.get('razorpay_order_id', '')
            razorpay_signature = data.get('razorpay_signature', '')

            order_id = data.get('order')
            order = Order.objects.filter(id=order_id).first()

            if not request.user.is_authenticated:
                print("User not authenticated")
                return JsonResponse({'success': False, 'message': 'User not authenticated'})

            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            }

            # Verify the payment signature
            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
                order.status = 'Processing'
                order.save()
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('order_success', kwargs={'order_id': order.id}),
                })
            except razorpay.errors.SignatureVerificationError:
                order.status = 'Payment Failed'
                order.save()
                return JsonResponse({
                    'success': False,
                    'message': 'Payment verification failed.',
                    'redirect_url': reverse('payment_failure', kwargs={'order_id': order.id}),
                })

        except json.JSONDecodeError:
            print("Invalid JSON format received")
            return JsonResponse({
                'success': False,
                'message': 'Invalid data received.',
                'redirect_url': reverse('payment_failure', kwargs={'order_id': order_id}),
            })
        except Exception as e:
            print("Error occurred:", e)
            return JsonResponse({
                'success': False,
                'message': f"An error occurred: {str(e)}",
                'redirect_url': reverse('payment_failure', kwargs={'order_id': order_id}),
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@never_cache
@login_required
def payment_failure(request, order_id):
    try:
        order = Order.objects.filter(id=order_id).first()
        if order:
            order.status = "Payment Failed"
            order.save()
            messages.error(request, "Payment Failed")
        else:
            messages.error(request, "Order not found. Payment Failure.")

    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('order_history')
    
    except Exception as e:
        print("Error occurred while processing payment failure:", e)
        messages.error(request, "An error occurred while processing your request.")

    context = {
        'order': order,
        'error': request.GET.get('error', 'An unknown error occurred.')
    }
    return render(request, 'User side/payment_failure.html', context)


def retry_payment(request,order_id):
    try:
        order = Order.objects.filter(id=order_id).first()
        razorpay_order_id = order.razorpay_order_id
        total_amount = order.total_amount
        discount_amount = order.discount
        amount = int(total_amount * 100)
        currency = 'INR'
        

        context = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                'order':order,
                'amount': amount,
                'currency': currency,
                'csrf_token': get_token(request),
                'discount_amount': discount_amount,
            }
        return render(request, 'User side/make_order.html', context=context)
    
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('order_detail', order_id=order_id)

    except ValueError as e:
        messages.error(request, str(e))
        return redirect('order_detail', order_id=order_id)
    
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('order_detail', order_id=order_id)


@never_cache
@login_required
def order_success(request, order_id):
    try:
        order = get_object_or_404(Order,id=order_id)
        context={
            'order':order,
        }
        return render(request, 'User side/order_success.html',context)
    except Http404:
        messages.error(request,"Order not Found")
        return redirect('home page')

@login_required
@never_cache
def download_invoice_pdf(request, order_id):
    try:
        order = order = get_object_or_404(Order,id=order_id)
        order_items = OrderItem.objects.filter(order=order)
        sub_total = 0
        for order_item in order_items:
            if order_item.is_listed:
                sub_total = sub_total + order_item.price

        context = {
            'order': order,
            'sub_total':sub_total,
            'colors':colors
        }

        # Render HTML content from template with context data
        html = render_to_string('User side/invoice_pdf.html', context)
        #config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

        config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')


        # Generate PDF from HTML using pdfkit
        pdf = pdfkit.from_string(html, False, configuration=config)

        # Create HTTP response with the PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

        return response
    except Http404:
        messages.error(request,"Order not Found")
        return redirect('order_history')

@login_required
@never_cache
def request_refund(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order_items=OrderItem.objects.filter(order=order).all()
        if order.status == 'Delivered' or order.payment_method == 'Razorpay' or order.payment_method == 'Wallet':
            order.refund_requested = True
            for order_item in order_items:
                order_item.refund_requested = True
                order_item.save()

            order.status = 'Refund processed'
            order.save()
            messages.success(request, "Refund request submitted successfully.")
        else:
            messages.error(request, "Order cannot be refunded.")
        return redirect('order_detail',order_id=order_id)
    except Http404:
        messages.error(request,"Order not Found")
        return redirect('order_history')

@login_required
@never_cache
def request_refund_item(request, item_id):
    try:
        order_item = get_object_or_404(OrderItem, id=item_id)
        order=order_item.order
        if order.status == 'Delivered' or order.payment_method == 'Razorpay' or order.payment_method == 'Wallet':
            order_item.refund_requested = True
            order_item.save()
            messages.success(request, "Refund request submitted successfully.")
        else:
            messages.error(request, "Order cannot be refunded.")
        return redirect('order_detail',order_id=order.id)
    except Http404:
        messages.error(request,"Order not Found")
        return redirect('order_history')
