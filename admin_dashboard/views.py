from django.contrib import messages
from django.shortcuts import redirect, render
from user_accounts.models import CustomUser
from user_profile.models import Wallet,WalletTransaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required,user_passes_test
from django.shortcuts import render 
from shop_cart.models import Order,OrderItem,Coupon
from admin_dashboard.models import ProductOffer
from categories.models import Category
from products.models import Variant,Product
from django.shortcuts import get_object_or_404
from products.utils import colors
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from django.utils.timezone import is_naive
from datetime import datetime, timedelta
from django.db.models import Sum,Count
from django.template.loader import render_to_string
from decimal import Decimal,InvalidOperation
from django.http import HttpResponse
import pandas as pd
from io import BytesIO
from django.db.models import Q,F
import pdfkit
from django.http import Http404
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

def is_user_superuser(user):
    return user.is_superuser

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def admin_dashboard(request):
    admin_user = request.session.get('admin_user', None)
    customers = CustomUser.objects.all()
    orders = Order.objects.all()

    filter_option = request.GET.get('filter','monthly')

    pending_order = orders.filter(status='Processing').count()
    delivered_order = orders.filter(status='Delivered').count()
    cancelled_order = orders.filter(Q(status='Cancelled') | Q(status='Refunded')).count()

    # Calculate revenue data based on filter option
    labels, revenue_data = calculate_revenue(filter_option)


    # Calculate total sales for all products
    total_sales = OrderItem.objects.aggregate(total_sales=Sum(F('quantity') * F('price')))['total_sales'] or 0

    # Calculate top-selling categories based on total sales
    top_selling_categories = Category.objects.annotate(
        total_sales=Sum(F('products__orderitem__quantity') * F('products__orderitem__price'))
    ).order_by('-total_sales')[:10]


    # Calculate top-selling products based on the total number of units sold
    top_selling_products = Product.objects.annotate(
        units_sold=Sum('orderitem__quantity'),
        total_revenue=Sum(F('orderitem__quantity') * F('orderitem__price'))
    ).order_by('-units_sold')[:10]


    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'revenue': revenue_data,
            'top_selling_categories': list(top_selling_categories.values('name', 'total_sales')),
            'top_selling_products': list(top_selling_products.values('name', 'units_sold', 'total_revenue')),
            'pending': pending_order,
            'delivered': delivered_order,
            'cancelled': cancelled_order,
            'labels': labels,
        }
        return JsonResponse(data)

    # Prepare context for rendering
    context = {
        'user_count': customers.count(),
        'order_count': orders.count(),
        'pending_order': pending_order,
        'delivered_order': delivered_order,
        'cancelled_order': cancelled_order,
        'admin': admin_user,
        'labels': labels,
        'revenue': revenue_data,
        'top_selling_categories': top_selling_categories,
        'top_selling_products': top_selling_products,
    }

    return render(request, 'Admin side/admin_dashboard.html', context)


def calculate_revenue(filter_option):
    now = timezone.now()
    labels = []
    revenue_data = []

    if filter_option == 'monthly':
        for month in range(1, 13):
            month_name = datetime(now.year, month, 1).strftime('%B')
            labels.append(month_name)
            revenue = Order.objects.filter(created_at__month=month, created_at__year=now.year).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0
            revenue_data.append(revenue)
    
    elif filter_option == 'weekly':
        start_date = now - timedelta(days=now.weekday())  # Start of the current week
        for i in range(6):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            labels.append(f"Week {i + 1}")
            revenue = Order.objects.filter(created_at__range=[week_start, week_end]).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0
            revenue_data.append(revenue)
    
    elif filter_option == 'yearly':
        for year in range(now.year - 1, now.year + 1):
            labels.append(str(year))
            revenue = Order.objects.filter(created_at__year=year).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0
            revenue_data.append(revenue)

    else:
        for month in range(1, 13):
            month_name = datetime(now.year, month, 1).strftime('%B')
            labels.append(month_name)
            revenue = Order.objects.filter(created_at__month=month, created_at__year=now.year).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0
            revenue_data.append(revenue)

    return labels, revenue_data


@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def admin_profile(request):
    return render(request,'Admin side/admin_profile.html')


@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def admin_orders(request):
    admin_user = request.session.get('admin_user', None)
    orders=Order.objects.all().order_by('-created_at')
    paginator = Paginator(orders,10)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    context={
        'page_obj':page_obj,
        'admin':admin_user,
    }
    return render(request,'Admin side/admin_orders.html',context)

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def admin_order_details(request,order_id):
    try:
        admin_user = request.session.get('admin_user', None)
        order = get_object_or_404(Order, id=order_id)
        orderItems = OrderItem.objects.filter(order=order)
        Del_charge = Decimal(50)
        sub_total = 0
        order_item_price =0
        for order_item in orderItems:
            if order_item.is_listed:
                order_item_price = order_item.price * order_item.quantity
                sub_total= sub_total + order_item_price

        context = {
            'admin':admin_user,
            'order':order,
            'orderItems':orderItems,
            'colors':colors,
            'sub_total':sub_total
        }
        return render(request, 'Admin side/admin_order_details.html',context)
    
    except Http404:
        messages.error(request,"Order not found")
        return redirect('admin_orders')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('admin_orders')
    

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def change_order_status(request,order_id):
    try:
        order=get_object_or_404(Order,id=order_id)
        if request.method == 'POST':
            status=request.POST.get('status')
            if status:
                if status == 'Cancelled' and order.payment_method != 'Cash on delivery':
                    wallet, created = Wallet.objects.get_or_create(user=order.user)
                    
                    if not isinstance(wallet.balance, Decimal):
                        wallet.balance = Decimal(wallet.balance)

                    wallet.balance += Decimal(order.total_amount)
                    wallet.save()

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=order.total_amount,
                        transaction_type='credit'
                    )

                    order.refund_granted = True
                    order.refunded_to_wallet = True
                    order.is_listed = False
                    order.status = "Refunded"
                    order.save()

                    order_items = OrderItem.objects.filter(order=order)
                    for order_item in order_items:
                        variant = order_item.variant
                        variant.stock = variant.stock + order_item.quantity
                        variant.save()

                    messages.success(request, "Refund approved and amount credited to wallet.")
                    return redirect('admin_order_details',order_id=order_id)
                order.status = status
                order.save()
                messages.success(request,"Order status changed successfuly")
                return redirect('admin_order_details',order_id=order_id)
            else:
                messages.success(request,"select a valid status")
                return redirect('admin_order_details',order_id=order_id)
        return redirect('admin_order_details',order_id=order_id)
    except Http404:
        messages.error(request,"Order not found")
        return redirect('admin_orders')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('admin_orders')

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def admin_coupons(request):
    coupons = Coupon.objects.all()
    for coupon in coupons:
        if coupon.valid_to < timezone.now() and coupon.active :
            coupon.active = False
            coupon.save()
            messages.error(request,'coupon date expired')
        
    paginator = Paginator(coupons, 10)  # Show 10 coupons per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context={
        'page_obj': page_obj,
    }

    return render(request,'Admin side/admin_coupons.html',context)

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        discount = request.POST.get('discount')
        min_amount = request.POST.get('min_amount')
        max_amount = request.POST.get('max_amount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')

        #string to date
        try:
            valid_from = datetime.strptime(valid_from, '%Y-%m-%d')
            valid_to = datetime.strptime(valid_to, '%Y-%m-%d')
            
            # Make the datetime objects timezone-aware
            valid_from = timezone.make_aware(valid_from, timezone.get_current_timezone())
            valid_to = timezone.make_aware(valid_to, timezone.get_current_timezone())

            if valid_from > valid_to :
                messages.error(request,'Invalid date')
                return redirect('admin_coupons')
            
            if Decimal(discount) > 99 or Decimal(discount) < 0 :
                messages.error(request,'Discount must be below 99% or above 1%')
                return redirect('admin_coupons')
            
            if code == ' ':
                messages.error(request,'in coupon code white spaces are not allowed')
                return redirect('admin_coupons')
            
            if min_amount > max_amount:
                messages.error(request,'check the amount')
                return redirect('admin_coupons')
            
            coupon = Coupon.objects.create(
            code=code,
            discount=discount,
            min_amount=min_amount,
            max_amount=max_amount,
            valid_from=valid_from,
            valid_to=valid_to,
            used=False
            )

            if coupon.valid_from <= timezone.now() <= coupon.valid_to:
                coupon.active = True
            else:
                coupon.active = False

            coupon.save() 
            return redirect('admin_coupons')

        except ValueError:
            messages.error(request, 'Invalid date format.')
            return render(request, 'User side/edit_coupon.html', {'coupon': coupon}) 
        
    return render(request,'Admin side/admin_coupons.html')

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def edit_coupon(request, coupon_id):
    try:
        coupon = get_object_or_404(Coupon, id=coupon_id)
        if request.method == 'POST':
            code = request.POST.get('coupon_code',coupon.code)
            min_amount = request.POST.get('min_amount',coupon.min_amount)
            max_amount = request.POST.get('max_amount',coupon.max_amount)
            discount_str = request.POST.get('discount',coupon.discount)
            valid_from = request.POST.get('valid_from')
            valid_to = request.POST.get('valid_to')

            try:
                # Convert valid_from to datetime only if it's provided as a string
                if isinstance(valid_from, str):
                    #string to date
                    valid_from_dt = datetime.strptime(valid_from, '%Y-%m-%d')
                    valid_from_dt = timezone.make_aware(valid_from_dt, timezone.get_current_timezone()) 
                else:
                    valid_from_dt = coupon.valid_from

                if isinstance(valid_to, str):
                    valid_to_dt = datetime.strptime(valid_to, '%Y-%m-%d')
                    valid_to_dt = timezone.make_aware(valid_to_dt, timezone.get_current_timezone())
                else:
                    valid_to_dt = coupon.valid_to

                if valid_from_dt and valid_to_dt and valid_from_dt > valid_to_dt :
                    messages.error(request,'Invalid date range')
                    return redirect('admin_coupons')
                
                discount = float(discount_str)
                min_amount = int(min_amount)
                max_amount = int(max_amount)

                if discount < 0:
                    messages.error(request, 'Discount cannot be negative.')
                    return redirect('admin_coupons')
                
                if discount > 99 :
                    messages.error(request,'Discount must be below 99%')
                    return redirect('admin_coupons')
                
                if min_amount > max_amount:
                    messages.error(request,'check the amount')
                    return redirect('admin_coupons')
                
                
                coupon.code = code
                coupon.min_amount = min_amount
                coupon.max_amount = max_amount
                coupon.discount = discount
                # Assign the validated dates to the coupon
                coupon.valid_from = valid_from_dt
                coupon.valid_to = valid_to_dt

                now = timezone.now()
                if valid_from_dt <= now <= valid_to_dt:
                    coupon.active = True
                else:
                    coupon.active = False

                coupon.save()
                messages.success(request,'Coupon updated successfully.')
                return redirect('admin_coupons')

            except ValueError:
                messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
                return render(request, 'Admin side/edit_coupon.html', {'coupon': coupon})
            
        return render(request, 'Admin side/edit_coupon.html', {'coupon': coupon})
    except Http404:
        messages.error(request,"Coupon not found")
        return redirect('admin_coupons')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('admin_coupons')

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def coupon_status(request, coupon_id):
    try:
        coupon = get_object_or_404(Coupon, id=coupon_id)
        if coupon.valid_to >= timezone.now() :
            coupon.active = not coupon.active
            coupon.save()
            if coupon.active:
                messages.success(request, f'Coupon "{coupon.code}" activated.')
            else:
                messages.success(request, f'Coupon "{coupon.code}" deactivated.')
        else:
            messages.error(request, f'Cannot activate coupon "{coupon.code}" it has expired.')
        return redirect('admin_coupons')
    except Http404:
        messages.error(request,"Coupon not found")
        return redirect('admin_coupons')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('admin_coupons')


@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def approve_refund(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        if order.refund_requested and not order.refund_granted:
            wallet, created = Wallet.objects.get_or_create(user=order.user)
            
            if not isinstance(wallet.balance, Decimal):
                wallet.balance = Decimal(wallet.balance)

            order_items = OrderItem.objects.filter(order=order)
            total = Decimal(0)
            for order_item in order_items:
                if order_item.refund_requested and not order_item.refund_granted:
                    item_price = order_item.price * order_item.quantity
                    total += item_price
                    order_item.refund_granted = True
                    order_item.save()

            total_refund = total + Decimal(order.tax_amount) + Decimal(50)
            wallet.balance += Decimal(total_refund)
            wallet.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                amount=total_refund,
                transaction_type='credit'
            )

            order.refund_granted = True
            order.refunded_to_wallet = True
            order.is_listed = False
            order.status = "Refunded"
            order.save()

            order_items = OrderItem.objects.filter(order=order)
            for order_item in order_items:
                order_item.is_listed = False
                order_item.save()
                variant = order_item.variant
                variant.stock = variant.stock + order_item.quantity
                variant.save()

            messages.success(request, "Refund approved and amount credited to wallet.")
            return redirect('admin_order_details',order_id=order_id)

        messages.error(request, "Refund cannot be processed.")
        return redirect('admin_order_details',order_id=order_id)
    except Http404:
        messages.error(request,"Order not found")
        return redirect('admin_orders')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('admin_orders')
    

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def approve_refund_item(request, item_id):
    try:
        order_item = get_object_or_404(OrderItem, id=item_id)
        order = order_item.order
        if order_item.refund_requested and not order_item.refund_granted:
            wallet, created = Wallet.objects.get_or_create(user=order.user)
            
            if not isinstance(wallet.balance, Decimal):
                wallet.balance = Decimal(wallet.balance)

            order_item_price = order_item.price * order_item.quantity

            wallet.balance += Decimal(order_item_price)
            wallet.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                amount=order_item_price,
                transaction_type='credit'
            )

            order_item.is_listed = False
            order_item.refund_granted = True
            order_item.save()
            order.total_amount= order.total_amount - order_item.price
            order.save()
            messages.success(request, "Refund approved and amount credited to wallet.")
            return redirect('admin_order_details',order_id=order.id)
        messages.error(request, "Refund cannot be processed.")
        return redirect('admin_order_details',order_id=order.id)
    except Http404:
        messages.error(request,"Order not found")
        return redirect('admin_orders')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('admin_orders')

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def admin_offers(request):
    product_offers = ProductOffer.objects.all()
    now = timezone.now()

    for offer in product_offers:
        if offer.valid_to < now and offer.is_active:
            offer.is_active = False
            offer.save()
            messages.info(request, f'Product offer "{offer}" has expired and was deactivated.')

    products = Product.objects.all()

    context = {
        "products": products,
        "product_offers": product_offers
    }
    return render(request, 'Admin side/admin_offers.html', context)


@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def add_product_offer(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        variant_color = request.POST.get('variant')
        percentage = request.POST.get('discount_percentage')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')

        # Validate inputs
        if not product_id or not product_id.strip():
            messages.error(request, 'Invalid product ID.')
            return redirect('admin_offers')

        if not variant_color or not variant_color.strip():
            messages.error(request, 'Variant selection is mandatory.')
            return redirect('admin_offers')

        try:
            percentage = Decimal(percentage)
            if percentage > 99 or percentage < 0:
                messages.error(request, 'Discount must be between 0% and 99%.')
                return redirect('admin_offers')
        except InvalidOperation:
            messages.error(request, 'Invalid discount percentage format.')
            return redirect('admin_offers')

        try:
            # Convert date strings to datetime objects
            valid_from = datetime.strptime(valid_from, '%Y-%m-%d')
            valid_to = datetime.strptime(valid_to, '%Y-%m-%d')

            # Make the datetime objects timezone-aware
            valid_from = timezone.make_aware(valid_from, timezone.get_current_timezone())
            valid_to = timezone.make_aware(valid_to, timezone.get_current_timezone())

            if valid_from > valid_to:
                messages.error(request, 'Invalid date range. "Valid From" must be before "Valid To".')
                return redirect('admin_offers')

        except ValueError:
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
            return redirect('admin_offers')

        try:
            # Fetch the product and variant
            product = Product.objects.get(id=product_id)
            variant = Variant.objects.get(color=variant_color, product=product)

        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')
            return redirect('admin_offers')

        except Variant.DoesNotExist:
            messages.error(request, 'Variant not found for the selected product.')
            return redirect('admin_offers')

        # Check if the selected variant already has an offer
        if ProductOffer.objects.filter(variant=variant).exists():
            messages.error(request, 'This variant already has an offer.')
            return redirect('admin_offers')

        # Create the product offer
        product_offer = ProductOffer(
            product=product,
            variant=variant,
            discount_percentage=percentage,
            valid_from=valid_from,
            valid_to=valid_to,
        )

        # Check if the offer is active
        now = timezone.now()
        if valid_from <= now <= valid_to:
            product_offer.is_active = True
        else:
            product_offer.is_active = False
        # Save the product offer
        product_offer.save()

        product.offer_applied = True
        product.save()

        messages.success(request, 'Offer created successfully.')
        return redirect('admin_offers')

    return render(request, 'Admin side/admin_offers.html')

from products.utils import colors

def get_color_name(hex_code):
    for name, code in colors:
        if code.lower() == hex_code.lower():
            return name
    return hex_code

@never_cache
def get_variants(request, product_id):
    variants = Variant.objects.filter(product_id=product_id)
    variants_info = [
        {'id': variant.id, 'color': variant.color, 'color_name': get_color_name(variant.color)} for variant in variants
    ]
    return JsonResponse({'variants': list(variants_info)})


@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def  change_product_offer_status(request,offer_id):
    try:
        offer = get_object_or_404(ProductOffer, id=offer_id)
        if offer.valid_to < timezone.now():
            messages.error(request, "This offer has expired.")
            return redirect('admin_offers')
        
        offer.is_active = not offer.is_active
        offer.save()

        product = offer.product
        
        product.offer_applied = offer.is_active
        product.save()

        if offer.is_active:
            messages.success(request, "Offer activated.")
        else:
            messages.success(request, "Offer deactivated.")

        return redirect('admin_offers')
    except Http404:
        messages.error(request,"Offer not found")
        return redirect('admin_offers')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('admin_offers')


@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def edit_product_offer(request,offer_id):
    try:
        offer = get_object_or_404(ProductOffer, id=offer_id)
        
        if request.method == 'POST':
            product_id = request.POST.get('product',offer.product.id)
            variant_id = request.POST.get('variant',offer.variant.id)
            percentage = request.POST.get('discount_percentage',offer.discount_percentage)
            valid_from = request.POST.get('valid_from',offer.valid_from)
            valid_to = request.POST.get('valid_to',offer.valid_to)

            try:
                if isinstance(valid_from, str):
                    valid_from = datetime.strptime(valid_from, '%Y-%m-%d')
                if isinstance(valid_to, str):
                    valid_to = datetime.strptime(valid_to, '%Y-%m-%d')

                # Make the datetime objects timezone-aware
                valid_from = timezone.make_aware(valid_from, timezone.get_current_timezone())
                valid_to = timezone.make_aware(valid_to, timezone.get_current_timezone())

                if not product_id:
                    messages.error(request, 'Invalid product ID.')
                    return redirect('admin_offers')

                if valid_from > valid_to:
                    messages.error(request, 'Invalid date range.')
                    return redirect('admin_offers')

                if Decimal(percentage) > 99 or Decimal(percentage) < 0:
                    messages.error(request, 'Discount must be between 0% and 99%.')
                    return redirect('admin_offers')

                product = Product.objects.get(id=product_id)
                variant = Variant.objects.get(id=variant_id) if variant_id else None

                # Update the offer details
                offer.product = product
                offer.variant = variant
                offer.discount_percentage = Decimal(percentage)
                offer.valid_from = valid_from
                offer.valid_to = valid_to

                product.offer_applied = True
                product.save()

                # Set offer status based on validity
                now = timezone.now()
                if valid_from <= now <= valid_to:
                    offer.is_active = True
                else:
                    offer.is_active = False

                offer.save()
                messages.success(request, 'Offer updated successfully.')
                return redirect('admin_offers',{'colors':colors})

            except ValueError:
                messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
                return redirect('admin_offers')
            except Product.DoesNotExist:
                messages.error(request, 'Product not found.')
                return redirect('admin_offers')
            except Variant.DoesNotExist:
                messages.error(request, 'Variant not found.')
                return redirect('admin_offers')

        # For GET request, populate form with current offer data
        products = Product.objects.all()
        variants = offer.product.variants.all() if offer.product else Variant.objects.none()

        context = {
            'offer': offer,
            'products': products,
            'variants': variants,
            'colors':colors
        }
        return render(request, 'Admin side/edit_product_offer.html', context)
    except Http404:
        messages.error(request,"Offer not found")
        return redirect('admin_offers')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('admin_offers')

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
def report(request):
    report_type = request.GET.get('report_type', 'day')

    # Determine the date truncation function based on the report type
    if report_type == 'day':
        date_trunc = TruncDate('created_at')
    elif report_type == 'week':
        date_trunc = TruncWeek('created_at')
    elif report_type == 'month':
        date_trunc = TruncMonth('created_at')
    else:
        date_trunc = TruncDate('created_at')  # Default to daily if unknown

    # Fetch aggregated orders data
    orders = Order.objects.annotate(
        date=date_trunc
    ).values(
        'date'
    ).annotate(
        total_orders=Count('id'),
        total_qty=Sum('order_items__quantity'),
        total_amount=Sum('order_items__price'),
        total_discount=Sum('discount'),
        profit=Sum('order_items__price') - Sum('discount')
    ).order_by('-date')

    # Pagination
    paginator = Paginator(orders, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Compute total values
    total_discount_amount = orders.aggregate(total_discount=Sum('discount'))['total_discount'] or 0
    total_sales_amount = orders.aggregate(total_sales=Sum('order_items__price'))['total_sales'] or 0
    total_profit = total_sales_amount - total_discount_amount

    if request.GET.get('generate_report') == '1':
        report_format = request.GET.get('report_format')
        context = {
            'orders': orders,
            'page_obj': page_obj,
            'report_type': report_type,
            'total_discount_amount': total_discount_amount,
            'total_sales_amount': total_sales_amount,
            'total_profit': total_profit,
        }
        if report_format == 'excel':
            return generate_excel_report(context)
        elif report_format == 'pdf':
            return generate_pdf_report(context)

    context = {
        'page_obj': page_obj,
        'report_type': report_type,
    }

    return render(request, 'Admin side/report.html', context)

    
def make_datetime_naive(df):
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.replace(tzinfo=None) if not is_naive(x) else x)
    return df

def generate_excel_report(context):
    # Extract the orders data from the context
    orders = context['orders']
    
    # Prepare the data structure with aggregated results
    data = [
        {
            'Date': item['date'].strftime('%Y-%m-%d') if item['date'] else '',
            'Total Orders': item['total_orders'],
            'Total Product QTY': item['total_qty'],
            'Total Order Amount': item['total_amount'],
            'Total Discount': item['total_discount'],
            'Profit': item['profit']
        }
        for item in orders
    ]
    
    # Convert the prepared data to a DataFrame
    df = pd.DataFrame(data)
    
    # Ensure all datetime values are timezone-naive
    df = make_datetime_naive(df)

    # Write the DataFrame to an Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Report', index=False)

        # Get the workbook and sheet
        workbook  = writer.book
        sheet = writer.sheets['Report']

        # Adjust column width based on the length of the data
        for column in sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)
            sheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=report.xlsx'
    return response

def generate_pdf_report(context):
    # Render HTML content from template with context data
    html = render_to_string('Admin side/report_pdf.html', context)

    # Path to wkhtmltopdf executable
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

    # Generate PDF from HTML using pdfkit
    pdf = pdfkit.from_string(html, False, configuration=config)

    # Create HTTP response with the PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    return response