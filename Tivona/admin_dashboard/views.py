from django.forms import ValidationError
from django.contrib import messages
from django.shortcuts import redirect, render
from user_accounts.models import CustomUser
from django.core.validators import validate_email
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required,user_passes_test
from django.shortcuts import render 
from shop_cart.models import Order,OrderItem,Coupon
from django.shortcuts import get_object_or_404
from products.utils import colors
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime

def is_superuser(user):
    return user.is_superuser

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_superuser)
def admin_dashboard(request):
    admin_user = request.session.get('admin_user',None)
    customers = CustomUser.objects.all()
    paginator = Paginator(customers,10)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    orders = Order.objects.all()
    order_count = len(orders)
    users_count = len(customers)
    pending_order=0
    for order in orders:
        if order.status == 'Pending':
            pending_order+=1
    
    context = {
        'page_obj': page_obj,
        'user_count': users_count,
        'order_count':order_count,
        'pending_order':pending_order,
        'admin': admin_user,
    }
    
    return render(request, 'Admin side/admin_dashboard.html', context)

@user_passes_test(is_superuser)
@login_required(login_url='/admin_login/')
@never_cache
def admin_profile(request):
    return render(request,'Admin side/admin_profile.html')


@user_passes_test(is_superuser)
@login_required(login_url='/admin_login/')
@never_cache
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

@user_passes_test(is_superuser)
@login_required(login_url='/admin_login/')
@never_cache
def admin_order_details(request,order_id):
    admin_user = request.session.get('admin_user', None)
    order = get_object_or_404(Order, id=order_id)
    orderItems = OrderItem.objects.filter(order=order)
    sub_total=(order.total_amount - order.tax_amount) + order.discount
    context = {
        'admin':admin_user,
        'order':order,
        'orderItems':orderItems,
        'colors':colors,
        'sub_total':sub_total
    }
    return render(request, 'Admin side/admin_order_details.html',context)

@login_required(login_url='/admin_login/')
def change_order_status(request,order_id):
    order=get_object_or_404(Order,id=order_id)
    if request.method == 'POST':
        status=request.POST.get('status')
        if status:
            order.status = status
            order.save()
            messages.success(request,"Order status changed successfuly")
            return redirect('admin_order_details',order_id=order_id)
        else:
            messages.success(request,"select a valid status")
            return redirect('admin_order_details',order_id=order_id)
    return redirect('admin_order_details',order_id=order_id)

@user_passes_test(is_superuser)
@login_required(login_url='/admin_login/')
@never_cache
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

        except ValueError:
            messages.error(request, 'Invalid date format.')
            return render(request, 'edit_coupon.html', {'coupon': coupon}) 
        

        coupon = Coupon.objects.create(
            code=code,
            discount=discount,
            min_amount=min_amount,
            max_amount=max_amount,
            valid_from=valid_from,
            valid_to=valid_to,
            used=False
        )

        if coupon.valid_from < timezone.now():
            coupon.active=True

        coupon.save() 

        return redirect('admin_coupons')
    return render(request,'Admin side/admin_coupons.html')

@never_cache
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        coupon.code = request.POST.get('coupon_code')
        coupon.discount = request.POST.get('discount')
        coupon.min_amount = request.POST.get('min_amount')
        coupon.max_amount = request.POST.get('max_amount')
        coupon.valid_from = request.POST.get('valid_from')
        coupon.valid_to = request.POST.get('valid_to')

        #string to date
        try:
            valid_from = datetime.strptime(valid_from, '%Y-%m-%d')
            valid_to = datetime.strptime(valid_to, '%Y-%m-%d')
            
            # Make the datetime objects timezone-aware
            valid_from = timezone.make_aware(valid_from, timezone.get_current_timezone())
            valid_to = timezone.make_aware(valid_to, timezone.get_current_timezone())

        except ValueError:
            messages.error(request, 'Invalid date format.')
            return render(request, 'edit_coupon.html', {'coupon': coupon}) 


        if coupon.valid_from < timezone.now():
            coupon.active=True

        if coupon.valid_to < timezone.now():
            coupon.active=False
        
        coupon.save()
        return redirect('admin_coupons')
    return render(request, 'Admin side/edit_coupon.html', {'coupon': coupon})

@never_cache
def coupon_status(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.active = not coupon.active
    coupon.save()
    return redirect('admin_coupons')

@user_passes_test(is_superuser)
@login_required(login_url='/admin_login/')
@never_cache
def banners(request):
    return render(request,'Admin side/banneres.html')

