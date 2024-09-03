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
from django.http import Http404
import time

@never_cache
def signup(request):
    try:
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
                return redirect('signup page')
            

            user = CustomUser.objects.create_user(username=uname, email=email, password=pass1,phone=phone)
            user.is_active = False #until email verification
            user.email_verified = False
            user.save()

            otp = generate_otp()
            send_otp_to_email(email, otp)
            
            return render(request, 'User side/otp.html', {
                'generated_otp': otp,
                'otp_timestamp': time.time(),
                'email': email,
                'user_id': user.id
            })

        return render(request,'User side/signup.html')
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('signup page')

@never_cache
def resend_otp(request):
    try:
        if request.method=='POST':
            user_id = request.POST.get('user_id')
            user = CustomUser.objects.get(id=user_id)
            email = user.email
            otp = generate_otp()
            send_otp_to_email(email, otp)
            
            return render(request, 'User side/otp.html', {
                'generated_otp': otp,
                'otp_timestamp': time.time(),
                'email': email,
                'user_id': user.id
            })
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('signup page')

@never_cache
def send_otp(request):
    try:
        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            user = CustomUser.objects.get(id=user_id)
            email = user.email
            generated_otp = request.POST.get('generated_otp')
            otp_timestamp = float(request.POST.get('otp_timestamp', 0))
            input_OTP = request.POST.get('otp')

            current_time = time.time()
            if current_time - otp_timestamp > 60:
                # OTP has expired
                messages.error(request, "OTP has expired, a new one has been sent.")
                otp = generate_otp()
                send_otp_to_email(email, otp)
                return render(request, 'User side/otp.html', {
                    'email': email, 
                    'generated_otp': otp, 
                    'otp_timestamp': time.time(),
                    'user_id': user.id
                    })
            
            if input_OTP == generated_otp:
                user.email_verified = True
                user.is_active = True
                user.save()
                backend='django.contrib.auth.backends.ModelBackend' # for multiple authentication confusion 
                login(request, user,backend=backend) # Log in the user with the specified backend
                messages.success(request, "Logged in Successfully")
                return redirect('home page')
            
            else:
                messages.error(request, "Invalid OTP")
                return render(request, 'User side/otp.html', {'email': email, 'duration': 60})

        return render(request, 'User side/otp.html', {'duration': 60})
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('signup page')


@never_cache
def loginn(request): 
    try: 
        if request.method == 'POST':
            username = request.POST.get('user')
            password = request.POST.get('password')
            
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.email_verified:
                    if not user.is_superuser:
                        if user.is_active:
                            backend='django.contrib.auth.backends.ModelBackend'
                            login(request, user,backend=backend)
                            messages.success(request, "Logged in Successfully")
                            return redirect('home page')
                        else:
                            messages.error(request, "User is Blocked")
                            return redirect('login page')
                    else:
                        messages.error(request, "Superuser login is not allowed")
                        return redirect('login page')
                else:
                    email = user.email
                    otp = generate_otp()
                    send_otp_to_email(email, otp)
            
                    return render(request, 'User side/otp.html', {
                        'generated_otp': otp,
                        'otp_timestamp': time.time(),
                        'email': email,
                        'user_id': user.id
                    })
            else:
                messages.error(request, "Invalid username or password")
                return redirect('login page')
            
        return render(request, 'User side/login.html')
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('login page')


@never_cache
@login_required
def logout(request):
    auth_logout(request)
    products=Product.objects.all()
    category=Category.objects.all()
    return render(request,'User side/index.html',{'products':products,'categories':category})

@never_cache
def forgot_password(request):
    try:
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
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('login page')

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
    try:
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
    
    except Http404:
        messages.error(request,"User not Found")
        return redirect('login page')
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('login page')

