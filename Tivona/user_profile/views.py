from django.shortcuts import render,redirect
from django.shortcuts import get_object_or_404
from categories.models import Category
from user_accounts.utils import is_valid_phone,is_strong_password
from django.contrib import messages
from user_accounts.models import CustomUser,Address
from shop_cart.models import Order,OrderItem
from datetime import timedelta
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from products.utils import colors
from django.core.paginator import Paginator
from user_profile.models import Wallet,WalletTransaction

# Create your views here.
@never_cache
@login_required
def profile(request,user_id):
    user = get_object_or_404(CustomUser,id=user_id)
    categories=Category.objects.all()
    return render(request,'User side/profile.html',{'categories':categories,'user':user})

@never_cache
@login_required
def update_profile(request,user_id):

    user = get_object_or_404(CustomUser,id=user_id)

    if request.method == 'POST':
        username = request.POST.get('username').strip()
        phone = request.POST.get('phone').replace(" ", "").strip()

        
        if not username.isalpha():
            messages.error(request,"username should contain only letters.")
            return redirect('update_profile',user_id=user_id)

        if not is_valid_phone(phone):
            messages.error(request, "Invalid phone number format. Please enter a valid phone number.")
            return redirect('update_profile',user_id=user_id)

        if CustomUser.objects.filter(username=username).exclude(id=user_id).exists():
            messages.error(request, "Username already exists! Try another username.")
            return redirect('update_profile',user_id=user_id)

        if CustomUser.objects.filter(phone=phone).exclude(id=user_id).exists():
            messages.error(request, "Phone number already exists.")
            return redirect('update_profile',user_id=user_id)
        
        user.username=username
        user.phone=phone
        user.save()
        messages.success(request,"Profile Updated successfully!")
        redirect('profile page',user_id=user_id)
        
    return render(request,'User side/update_profile.html',{'user':user})

@never_cache
@login_required
def address(request,user_id):
    user=get_object_or_404(CustomUser,id=user_id)
    categories= Category.objects.all()
    address=Address.objects.filter(user_id=user_id)
    return render(request,'User side/address_manage.html',{'user':user,'categories':categories,'addresses':address})


from django.http import JsonResponse
from geopy.geocoders import Nominatim

def get_address_details(pin_code):
    geolocator = Nominatim(user_agent="user_profile")
    try:
        location = geolocator.geocode(pin_code)
        if location:
            address = location.raw['address']
            city = address.get('city', '')
            state = address.get('state', '')
            country = address.get('country', '')
            return JsonResponse({'status': 'success', 'city': city, 'state': state, 'country': country})
        else:
            return JsonResponse({'status': 'fail', 'message': 'Location not found'})
    except Exception as e:
        return JsonResponse({'status': 'fail', 'message': str(e)})

@never_cache
@login_required
def add_address(request,user_id):
    if request.method == 'POST':
        customer_name=request.POST.get('name').strip()
        customer_phone=request.POST.get('phone').replace(" ", "").strip()
        customer_address=request.POST.get('address').strip()
        street=request.POST.get('street').strip()
        city=request.POST.get('city').strip()
        state=request.POST.get('state').strip()
        pin_code=request.POST.get('pin_code').replace(" ", "").strip()
        country=request.POST.get('country').strip()
        source_page = request.POST.get('source_page')

        user=get_object_or_404(CustomUser,id=user_id)

        if not all([customer_name,customer_phone,customer_address,street,city,state,pin_code,country]):
            if source_page == 'make_order':
                messages.error(request, "All fields are required.")
                return redirect ('make_order',{'address':address})   
            else:
                messages.error(request, "All fields are required.")
                return redirect('address_manage',user_id=user_id)

        if '00000000' in customer_phone:
            if source_page == 'make_order':
                messages.error(request, "Invalid number format. Please enter a valid phone number.")
                return redirect ('make_order',{'address':address})   
            else:
                messages.error(request, "Invalid number format. Please enter a valid phone number.")
                return redirect('address_manage',user_id=user_id)

        if not is_valid_phone(customer_phone):
            if source_page == 'make_order':
                messages.error(request, "Invalid phone number format. Please enter a valid phone number.")
                return redirect ('make_order',{'address':address})
            else:
                messages.error(request, "Invalid phone number format. Please enter a valid phone number.")
                return redirect('address_manage',user_id=user_id)
        
        if not city.isalpha() or not state.isalpha() or not country.isalpha():
            if source_page == 'make_order':
                messages.error(request,"city or state or country should contain only letters.")
                return redirect ('make_order',{'address':address})   
            else:
                messages.error(request,"city or state or country should contain only letters.")
                return redirect('address_manage',user_id=user_id)
        
        if not pin_code.isdigit() or len(pin_code) != 6: 
            if source_page == 'make_order':
                messages.error(request,"Invalid pin code. Please enter a valid 6-digit pin code.")
                return redirect ('make_order',{'address':address})   
            else:
                messages.error(request,"Invalid pin code. Please enter a valid 6-digit pin code.")
                return redirect('address_manage',user_id=user_id)

        #change the existing primary address as normal address
        Address.objects.filter(user_id=user_id,primary_address=True).update(primary_address=False)

        Address.objects.create(
            name=customer_name,
            phone=customer_phone,
            address=customer_address,
            street=street,
            city=city,
            state=state,
            pin_code=pin_code,
            country=country,
            user=user,
            primary_address=True
            )
        if source_page == 'make_order':
            messages.success(request, "Address added successfully.")
            return redirect ('make_order')   
        else:
            messages.success(request, "Address added successfully.")
            return redirect('address_manage',user_id=user_id)
    
    address = Address.objects.filter(user_id=user_id)
    categories= Category.objects.all()
    return render(request,'User side/address_manage.html',{'user':user,'categories':categories,'addresses':address})

@never_cache
@login_required
def edit_address(request,address_id):

    address=get_object_or_404(Address,id=address_id)
    user_id=address.user_id

    if request.method == 'POST':
        customer_name=request.POST.get('name',address.name).strip()
        customer_phone=request.POST.get('phone',address.phone).replace(" ", "").strip()
        customer_address=request.POST.get('address',address.address).strip()
        street=request.POST.get('street',address.street).strip()
        city=request.POST.get('city',address.city).strip()
        state=request.POST.get('state',address.state).strip()
        pin_code=request.POST.get('pin_code',address.pin_code).strip()
        country=request.POST.get('country',address.country).strip()
        source_page = request.POST.get('source_page') 


        if not all([customer_name,customer_phone,customer_address,street,city,state,pin_code,country]):
            messages.error(request, "All fields are required.")
            return redirect('address_manage',user_id=user_id)

        if '00000000' in customer_phone:
            messages.error(request, "Incorrect phone number.")
            if source_page == 'make_order':
                return redirect('make_order')
            else:
                return redirect('address_manage', user_id=request.user.id)

        if not is_valid_phone(customer_phone):
            messages.error(request, "Invalid phone number format. Please enter a valid phone number.")
            return redirect('address_manage',user_id=user_id)
        
        if not city.isalpha() or not state.isalpha() or not country.isalpha():
            messages.error(request,"city or state or country should contain only letters.")
            return redirect('address_manage',user_id=user_id)
        
        if not pin_code.isdigit() or len(pin_code) != 6:
            messages.error(request,"Invalid pin code. Please enter a valid 6-digit pin code.") 
            return redirect('address_manage',user_id=user_id)
        
        
        address.name = customer_name
        address.phone = customer_phone
        address.address = customer_address
        address.street = street
        address.city = city
        address.state = state
        address.pin_code = pin_code
        address.country = country
        address.save()
        messages.success(request,"Address edit successfully")
        if source_page == 'make_order':
            return redirect('make_order')
        else:
            return redirect('address_manage', user_id=request.user.id)
        
    user=get_object_or_404(CustomUser,id=user_id)
    categories = Category.objects.all()
    return render(request, 'User side/edit_address.html',{'user':user,'address': address,'categories': categories})

@never_cache 
@login_required       
def delete_address(request, address_id):
    address = get_object_or_404(Address,id=address_id)
    user_id = address.user_id

    if request.method == 'POST':
        address.is_listed = not address.is_listed  # Toggle the is_listed flag
        address.primary_address=False
        address.save() 
        addresses = Address.objects.filter(user_id=user_id)
        if not addresses.filter(primary_address=True).exists() and addresses.exists():
            last_address = addresses.last()
            last_address.primary_address = True
            last_address.save()
        return redirect('address_manage',user_id=user_id)
    
    return redirect('address_manage',user_id=user_id)

@never_cache
@login_required
def change_password(request,user_id):

    user = get_object_or_404(CustomUser,id=user_id)
    if request.method == 'POST':
        current_password = request.POST.get('currentpass')
        new_password = request.POST.get('newpass')
        confirm_password = request.POST.get('confirmpass')

        # Validate inputs
        if not user.check_password(current_password):
            messages.error(request,"Current password is incorrect.")
            return render(request, 'User side/change_password.html',{'user_id': user_id})

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return render(request, 'User side/change_password.html',{'user_id': user_id})

        if not is_strong_password(new_password):
            messages.error(request, "Password must be at least 8 characters long, contain letters, numbers, and special characters.")
            return render(request, 'User side/change_password.html',{'user_id': user_id})
        
        if not current_password or not new_password or not confirm_password:
            messages.error(request, "All fields are required.")
            return render(request,'User side/change_password.html',{'user_id':user_id})

        # Change password
        user.set_password(new_password)
        user.save()
        # Update session authentication hash
        update_session_auth_hash(request,user)

        messages.success(request, "Password changed successfully!")
        return redirect('profile page',user_id=user_id)
    
    categories= Category.objects.all()
    return render(request, 'User side/change_password.html',{'user_id': user_id,'categories':categories})

@never_cache
@login_required
def order_history(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    paginator = Paginator(orders,5)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    context={
        'page_obj':page_obj,
    }
    return render(request, 'User side/order_history.html',context)

@login_required
@never_cache
def order_detail(request,order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order) 
    sub_total = (order.total_amount + order.discount) - order.tax_amount 
    expected_date = order.created_at + timedelta(days=5)
    context = {
        'order': order,
        'order_items':order_items,
        'expected_date':expected_date,
        'sub_total':sub_total,
        'colors':colors
    }
    return render(request,'User side/order_detail.html',context)

@login_required
def order_cancel(request,order_id):
    order=get_object_or_404(Order,pk=order_id)
    if request.method=='POST':
        order.is_listed = not order.is_listed
        order.status=" order cancelled " 
        order.save()
        order_items = OrderItem.objects.filter(order=order)
        for order_item in order_items:
            variant = order_item.variant
            variant.stock = variant.stock + order_item.quantity
            variant.save()

        return redirect('order_history')
    return redirect('order_history')
    
@never_cache
@login_required
def wallet_details(request):
    user = request.user
    wallet = Wallet.objects.filter(user=user).first()
    context = {
        'balance_amount' : wallet.balance if wallet else 0
    }
    return render(request,'User side/wallet.html',context)

@never_cache
@login_required
def wallet_transactions(request):
    user = request.user
    wallet = Wallet.objects.filter(user=user).first()

    transactions = WalletTransaction.objects.filter(wallet=wallet)

    context = {
        'transactions' : transactions,
        'balance_amount' : wallet.balance
    }
    return render(request,'User side/wallet_transactions.html',context)

