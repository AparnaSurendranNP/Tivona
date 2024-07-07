from django.shortcuts import render
from django.views.decorators.cache import never_cache
from categories.models import Category
from products.models import Product

# Create your views here.

@never_cache
def index(request):
    categories=Category.objects.all()
    products=Product.objects.all()
    return render(request,'User side/index.html',{'categories':categories,'products':products})

@never_cache
def shop(request):
    categories=Category.objects.all()
    products=Product.objects.all()
    return render(request,'User side/shop-grid.html',{'categories':categories,'products':products})

@never_cache
def contact(request):
    return render(request,'User side/contact.html')

