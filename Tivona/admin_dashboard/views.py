from django.forms import ValidationError
from django.shortcuts import redirect, render
from user_accounts.models import CustomUser
from django.core.validators import validate_email
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.shortcuts import render 

@never_cache
@login_required(login_url='/admin_login/')
def admin_dashboard(request):
    admin_user = request.session.get('admin_user', None)
    
    # Fetch all users and get the count
    clients = CustomUser.objects.all()
    users_count = len(clients)
    
    context = {
        'customers': clients,
        'user_count': users_count,
        'admin': admin_user,
    }
    
    return render(request, 'Admin side/admin_dashboard.html', context)

def admin_profile(request):
    return render(request,'Admin side/admin_profile.html')

def admin_orders(request):
    return render(request,'Admin side/admin_orders.html')

def admin_coupons(request):
    return render(request,'Admin side/admin_coupons.html')

def banners(request):
    return render(request,'Admin side/banneres.html')

