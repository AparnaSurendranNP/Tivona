from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from .models import CustomUser
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from .utils import is_valid_phone,is_strong_password,is_valid_email,generate_otp,send_otp_to_email
from products.models import Product
from categories.models import Category
from django.shortcuts import get_object_or_404
import time

@never_cache
def signup(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        phone=request.POST.get('phone')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            messages.error(request, "Passwords don't match!!")
            return redirect('signup page')

        if " " in uname or " " in email or " " in pass1 or " " in phone:
            messages.error(request, "White Spaces are not allowed")
            return redirect('signup page')
        
        if not is_strong_password(pass1):
            messages.error(request, "Password must be at least 8 characters long, contain letters, numbers, and special characters.")
            return redirect('signup page')

        if not is_valid_phone(phone):
            messages.error(request, "Invalid phone number format. Please enter a valid phone number.")
            return redirect('signup page')

        if CustomUser.objects.filter(username=uname):
            messages.error(request, "Username already exists! Try another username.")
            return redirect('signup page')

        if not is_valid_email(email):
            messages.error(request, "Invalid email format. Please enter a valid email address.")
            return redirect('signup_page')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('signup page')
        
        if CustomUser.objects.filter(phone=phone).exists():
            messages.error(request, "Phone Number already exists.")
        
        else:
            otp = generate_otp()
            send_otp_to_email(email, otp)
            request.session['otp_timestamp'] = time.time()
            request.session['otp'] = otp
            request.session['email'] = email
            request.session['username'] = uname
            request.session['phone'] = phone
            request.session['password'] = pass1
            return render(request, 'User side/otp.html')

    return render(request,'User side/signup.html')

@never_cache
def resend_otp(request):
    if request.method=='POST':
        email = request.session.get('email')
        otp = generate_otp()
        request.session['otp'] = otp
        request.session['otp_timestamp'] = time.time()
        send_otp_to_email(email, otp)
        return render(request, 'User side/otp.html', {'duration': 60})   

@never_cache
def send_otp(request):
    if request.method == 'POST':
        email = request.session.get('email')
        otp_timestamp = request.session.get('otp_timestamp', 0)
        generated_otp = request.session.get('otp')
        input_OTP = request.POST.get('otp')

        current_time = time.time()
        if current_time - otp_timestamp > 60:
            # OTP has expired
            messages.error(request, "OTP has been expired , we already send new one" )
            del request.session['otp']
            del request.session['otp_timestamp']
            resend_otp(request)
            return render(request, 'User side/otp.html', {'email': email})
        
        if input_OTP == generated_otp:
            user = request.session.get('username')
            phone=request.session.get('phone')
            password = request.session.get('password')
            
            user = CustomUser.objects.create_user(username=user, email=email, password=password,phone=phone)
            user.save()

            # Clear session data
            del request.session['otp']
            del request.session['username']
            del request.session['email']
            del request.session['password']
            del request.session['phone']
            
            # Authenticate and log in the user
            user = authenticate(request, username=user, password=password)
            if user is not None:
                login(request,user)
                messages.success(request, "Logined Successfully")
                return redirect('home page')
            else:
                messages.error(request, "There was an error logging you in. Please try logging in manually.")
                return redirect('login page')
        
        else:
            messages.error(request, "Invalid OTP")
            return render(request, 'User side/otp.html', {'email': email, 'duration': 60}) 

    return render(request, 'User side/otp.html', {'duration': 60})


@never_cache
def loginn(request):
     
    if request.method == 'POST':
        username = request.POST.get('user')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and not user.is_superuser:

            if user.is_active:
                login(request, user)
                messages.success(request, "Logined Successfully")
                return redirect('home page')
            else:
                messages.error(request,"User is Blocked")
                return redirect('login page')
            
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login page')
        
    return render(request,'User side/login.html')


@never_cache
@login_required
def logout(request):
    auth_logout(request)
    products=Product.objects.all()
    category=Category.objects.all()
    return render(request,'User side/index.html',{'products':products,'categories':category})

@never_cache
def forgot_password(request):

    if request.method == 'POST':
        email = request.POST.get('email')

        if not is_valid_email(email):
            messages.error(request, "Invalid email format. Please enter a valid email address.")
            return redirect('forgot_password')

        user = CustomUser.objects.filter(email=email).first()
        if not user:
            messages.error(request, "No user found with this email address.")
            return redirect('forgot_password')

        otp = generate_otp()
        send_otp_to_email(email, otp)
        request.session['otp'] = otp
        request.session['email'] = email
        request.session['user_id'] = user.id
        return redirect('forgot_otp')
        
    return render(request, 'User side/forgot_password.html')

@never_cache
def forgot_otp(request):
    if request.method == 'POST':
        email = request.session.get('email')
        user_id = request.session.get('user_id')
        generated_otp = request.session.get('otp')
        input_otp = request.POST.get('otp')

        if input_otp == generated_otp:
            return redirect('set_password')
        else:
            messages.error(request, "Invalid OTP")
            return render(request, 'User side/forgot_otp.html', {'email': email, 'duration': 60})

    return render(request, 'User side/forgot_otp.html', {'duration': 60})

@never_cache
def forgot_resend_otp(request):
    if request.method=='POST':
        email = request.session.get('email')
        otp = generate_otp()
        request.session['otp'] = otp
        send_otp_to_email(email, otp)
        return render(request, 'User side/forgot_otp.html', {'duration': 60})   

@never_cache
def set_password(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            messages.error(request, "Passwords don't match!")
            return redirect('set_password')

        if not is_strong_password(pass1):
            messages.error(request, "Password must be at least 8 characters long, contain letters, numbers, and special characters.")
            return redirect('set_password')

        user = get_object_or_404(CustomUser, id=user_id)
        user.set_password(pass1)
        user.save()
        messages.success(request, "Password reset successfully. You can now log in with your new password.")
        if user.is_staff:
            return redirect('admin_login page')
        else:
            return redirect('login page')

    return render(request, 'User side/set_password.html')

