from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from categories.models import Category
from products.models import Product,Variant
from shop_cart.models import Cart,CartItem
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Min
from django.http import JsonResponse

# Create your views here.

@never_cache
def index(request):
    categories=Category.objects.all()
    products=Product.objects.all().order_by('name')[:12]
    latest_products=Product.objects.all().order_by('-id')[:4]
    context={
        'categories':categories,
        'products':products,
        'latest_products':latest_products,
    }
    return render(request,'User side/index.html',context)

@never_cache
def shop(request): 
    categories=Category.objects.all()
    sort_option=request.GET.get('sort','name')
    min_price = request.GET.get('min_price', 99)
    max_price = request.GET.get('max_price', 1000)

    products=Product.objects.all()
    products = products.annotate(min_price=Min('variants__price'))

    products = products.filter(min_price__gte=min_price, min_price__lte=max_price)

    if sort_option == 'name':
        products=products.order_by('name')
    elif sort_option == 'price':
        products=products.order_by('min_price')
    elif sort_option == '-price':
        products=products.order_by('-min_price')
    elif sort_option == 'created_at':
        products=products.order_by('-id')

    latest_products=Product.objects.all().order_by('-id')

    paginator=Paginator(products,9)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)

    context={
        'categories':categories,
        'page_obj':page_obj,
        'sort_option': sort_option,
        'min_price': min_price,
        'max_price': max_price,
        'latest_products':latest_products,
    }
    return render(request,'User side/shop-grid.html',context)

def search(request):
    query = request.GET.get('search')
    products = Product.objects.filter(name__icontains=query)
    product = products.filter(name__iexact=query).first()
    
    suggestions = products.exclude(id=product.id) if product else products
    
    variants = Variant.objects.filter(product=product) if product else []
    
    context = {
        'product': product,
        'variants':variants,
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'User side/shop-details.html', context)

def suggest_products(request):
    query = request.GET.get('search', '')
    if query:
        suggestions = Product.objects.filter(name__icontains=query)[:10]
        suggestion_list = list(suggestions.values('id', 'name'))
        return JsonResponse(suggestion_list, safe=False)
    return JsonResponse([], safe=False)

@never_cache
def contact(request):
    return render(request,'User side/contact.html')

