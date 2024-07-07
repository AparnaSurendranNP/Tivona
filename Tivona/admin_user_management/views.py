from django.shortcuts import render
from django.forms import ValidationError
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.contrib import messages
from user_accounts.models import CustomUser
from django.contrib.auth import authenticate, login
from django.views.decorators.cache import never_cache
from django.core.validators import validate_email
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
import random
from django.http import Http404


# Create your views here.

from django.shortcuts import render, redirect, get_object_or_404


@login_required(login_url='/admin_login/')
@never_cache
def block_user(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, pk=pk)
        
        # Toggle user's active status
        user.is_active = not user.is_active
        user.save()
        return redirect('admin_view_users')
    
    customers=CustomUser.objects.all()
    return render(request,'Admin side/admin_view_users.html',{'customers':customers})

@never_cache
@login_required(login_url='/admin_login/')
def admin_users(request):
    client=CustomUser.objects.all()
    context={
        'customers':client
    }
    return render(request,'Admin side/admin_view_users.html',context)
