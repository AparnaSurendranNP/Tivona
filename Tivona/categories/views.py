from django.shortcuts import render,redirect
from django.shortcuts import get_object_or_404
from .models import Category
from django.utils.text import slugify
from products.models import Product
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages


@never_cache
def category_detail(request, category_slug):
    # Fetch the category based on the slug
    category = get_object_or_404(Category, slug=category_slug)
    
    
    products = Product.objects.filter(category=category)
    
    categories = Category.objects.all()
   
    context = {
        'categories':categories,
        'category': category,
        'products': products,
    }
    
    return render(request,'User side/category_detail.html', context)


@never_cache
@login_required(login_url='/admin_login/')
def admin_categories(request):
    categories=Category.objects.all()
    context={
        'categories':categories
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

            category.product_count = category.product.count()
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
        return redirect('admin_categories') 
    
    return render(request, 'Admin side/admin_categories.html', {'category': category})

@never_cache
@login_required(login_url='/admin_login/')
def edit_category(request, category_id):
    category = get_object_or_404(Category,id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('category_name')
        category.description = request.POST.get('category_description')
        
        if 'category_image' in request.FILES:
            category.image = request.FILES['category_image']
        
        category.save()
        return redirect('admin_categories') 
    
    return render(request, 'Admin side/edit_category.html', {'category': category})