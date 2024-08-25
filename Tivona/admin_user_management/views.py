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
from django.contrib.auth.decorators import login_required,user_passes_test
import random
from django.http import Http404
from django.core.paginator import Paginator


# Create your views here.

from django.shortcuts import render, redirect, get_object_or_404

def is_user_superuser(user):
    return user.is_superuser

@never_cache
@login_required(login_url='/admin_login/')
@user_passes_test(is_user_superuser)
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
@user_passes_test(is_user_superuser)
def admin_users(request):
    customers=CustomUser.objects.all()
    paginator = Paginator(customers,10)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    admin_user = request.session.get('admin_user', None)
    context={
        'page_obj':page_obj,
        'admin':admin_user
    }
    return render(request,'Admin side/admin_view_users.html',context)
