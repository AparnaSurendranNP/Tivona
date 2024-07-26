from django.shortcuts import render,redirect
from django.shortcuts import get_object_or_404
from .models import Category
from django.utils.text import slugify
from products.models import Product,Variant
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Min
from django.contrib import messages
from django.core.paginator import Paginator
from decimal import Decimal, InvalidOperation


@never_cache
def category_detail(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    sort_option=request.GET.get('sort','name')
    min_price = request.GET.get('min_price', 99)
    max_price = request.GET.get('max_price', 1000)

    try:
        min_price = Decimal(min_price)
        max_price = Decimal(max_price)
    except (InvalidOperation, ValueError):
        min_price = Decimal('99')
        max_price = Decimal('1000')
    
    products=Product.objects.filter(category=category)
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

    product_count=products.count()
    paginator=Paginator(products,9) # display 9 products in a page
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)

     
    categories = Category.objects.all()
    latest_products=Product.objects.all().order_by('-id')
   
    context = {
        'categories':categories,
        'category': category,
        'product_count':product_count,
        'sort_option': sort_option,
        'min_price': min_price,
        'max_price': max_price,
        'page_obj':page_obj,
        'latest_products':latest_products,
    }
    
    return render(request,'User side/category_detail.html', context)


@never_cache
@login_required(login_url='/admin_login/')
def admin_categories(request):
    admin_user = request.session.get('admin_user', None)
    categories=Category.objects.all()
    paginator = Paginator(categories,4)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    context={
        'page_obj':page_obj,
        'admin':admin_user,
    }
    return render(request,'Admin side/admin_categories.html',context)


@never_cache
@login_required(login_url='/admin_login/')
def add_category(request):
    if request.method == 'POST':
        cat_name = request.POST.get('category_name')
        description = request.POST.get('category_description')
        image = request.FILES.get('category_image')

        if cat_name == "" or description =="" or image == None:
            messages.error(request,"Please provide all required fields." )
            return redirect('admin_categories')
        
        if Category.objects.filter(name=cat_name).exists():
            messages.error(request, "Category already exit")
            return redirect('admin_categories')
        
        url_name = slugify(cat_name)

        try:
            category = Category.objects.create(
                name=cat_name,
                image=image,
                description=description,
                url_name=url_name
            )

            category.product_count = Variant.objects.filter(product__category=category).count()
            category.save()
            
            success_message = "Category added successfully."
            messages.success(request, success_message)
            return render('admin_categories')
        
        except Exception as e:
            error_message = f"Error occurred while adding category: {str(e)}"
            messages.error(request, error_message)
        
    category=Category.objects.all()
    return render(request, 'Admin side/admin_categories.html',{'categories':category})

@never_cache
@login_required(login_url='/admin_login/')
def unlist_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    
    if request.method == 'POST':
        category.is_listed = not category.is_listed  # Toggle the is_listed flag
        category.save()
        products=Product.objects.filter(category=category)
        for product in products:
            product.is_listed = not product.is_listed
            product.save()
        return redirect('admin_categories') 
    
    return render(request, 'Admin side/admin_categories.html', {'category': category})

@never_cache
@login_required(login_url='/admin_login/')
def edit_category(request, category_id):
    admin_user = request.session.get('admin_user', None)
    category = get_object_or_404(Category,id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('category_name')
        category.description = request.POST.get('category_description')
        
        if 'category_image' in request.FILES:
            category.image = request.FILES['category_image']
        
        category.save()
        return redirect('admin_categories') 

    context={
        'category':category,
        'admin':admin_user
    }
    
    return render(request, 'Admin side/edit_category.html',context)