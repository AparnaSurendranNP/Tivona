from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.core.validators import validate_email
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.conf import settings

@never_cache
def admin_login(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        passw = request.POST.get('passwordd')
        admin = authenticate(request, username=uname, password=passw)

        if admin is not None and admin.is_superuser:
            login(request,admin)
            request.session['admin_user'] = uname
            return redirect('admin_dashboard')
        
        elif admin is not None:
            # Handle regular user login or show error
            messages.error(request, "You are not authorized to access the admin dashboard.")
            return redirect('admin_login')
        
        else:
            messages.error(request, "Invalid username or password")
            return redirect('admin_login')
        
    return render(request,'Admin side/admin_login.html')
    
@never_cache
def admin_forgot_password(request):
    return render(request,'Admin side/admin_forgot_password.html')

@never_cache
@login_required(login_url='/admin_login/')
def logout(request):
    auth_logout(request)
    return render(request,'Admin side/admin_login.html')
