# Create your views here.
from django.shortcuts import render
from django.shortcuts import render,redirect
from .models import Product,ProductImage
from categories.models import Category
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from .models import Product, ProductImage,Variant
import base64
from django.core.files.base import ContentFile
from io import BytesIO
from django.utils.text import slugify
import time
from .utils import colors
from django.http import JsonResponse


@never_cache
def product_detail(request,product_slug):
    product = get_object_or_404(Product,slug=product_slug)
    variants = product.variants.filter(product=product)
    categories= Category.objects.all()
    return render(request, 'User side/shop-details.html', {'product': product,'categories':categories,'variants':variants})

def fetch_variant_images(request):
    variant_id = request.GET.get('variant_id')
    variant = get_object_or_404(Variant, id=variant_id)
    images = variant.images.all()
    image_urls = [image.image.url for image in images]
    return JsonResponse({'images': image_urls})

@login_required(login_url='/admin_login/')
def unlist_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        product.is_listed = not product.is_listed  # Toggle the is_listed flag
        product.save()
        return redirect('admin_products') 
    
    products=Product.objects.all()
    return render(request, 'Admin side/admin_products.html', {'products': products})


@never_cache
@login_required(login_url='/admin_login/')
def admin_products(request):
    products=Product.objects.all()
    categories=Category.objects.all()
    context={
        'products':products ,
        'categories':categories,
        'colors':colors,
    }
    return render(request,'Admin side/admin_products.html',context)


@login_required(login_url='/admin_login/')
def add_products(request):
    if request.method == 'POST':
        name = request.POST.get('product_name')
        description = request.POST.get('product_description')
        color = request.POST.get('product_color')
        price = request.POST.get('product_price')
        stock = request.POST.get('stock')
        category_id = request.POST.get('product_category')
        category = Category.objects.get(id=category_id)

        cropped_image_data = request.POST.get('croppedImage')
        if cropped_image_data:
            cropped_image_data = base64.b64decode(cropped_image_data)
            cropped_image_name = f'{slugify(name)}_{int(time.time())}.jpg'
            cropped_image = ContentFile(cropped_image_data, name=cropped_image_name)
        else:
            return render(request, 'Admin side/admin_products.html', {'error': 'Main image is required.'})

        product = Product.objects.create(
            name=name,
            image=cropped_image,
            description=description,
            product_count=0,
            category=category,
        )

        variant = Variant.objects.create(
            color=color,
            price=price,
            stock=stock,
            product=product,
        )

        product.product_count = sum(variant.stock for variant in product.variants.all())
        product.save()

        extra_cropped_images = request.POST.getlist('additional_cropped_images[]')
        for index, img_data in enumerate(extra_cropped_images):
            if img_data:
                img_data = base64.b64decode(img_data)
                additional_image_name = f'{slugify(name)}_additional_{index}_{int(time.time())}.jpg'
                img = ContentFile(img_data, name=additional_image_name)
                existing_images = ProductImage.objects.filter(variant=variant, image__exact=img)
                if not existing_images.exists():
                    ProductImage.objects.create(variant=variant, image=img)
            else:
                print(f"Empty image data at index {index}")

        category.product_count = sum(product.product_count for product in category.products.all())
        category.save()
        return redirect('admin_products')

    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, 'Admin side/admin_products.html', {'categories': categories, 'products': products})


@login_required(login_url='/admin_login/')
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = Variant.objects.filter(product_id=product_id)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('product_name')
        product.description = request.POST.get('product_description')
        category_id = request.POST.get('product_category')
        category = get_object_or_404(Category, id=category_id)
        product.category = category

        for variant in variants:
            variant.price = request.POST.get('variant_price')
            variant.color = request.POST.get('variant_color')
            variant.stock = request.POST.get('variant_stock')
            variant.save()

        if 'product_image' in request.FILES:
            product.image = request.FILES['product_image']

        if request.POST.get('croppedImage'):
            cropped_image_data = request.POST.get('croppedImage')
            format, imgstr = cropped_image_data.split(';base64,')
            ext = format.split('/')[-1]
            product.image.save(f'product_{product.id}.{ext}', ContentFile(base64.b64decode(imgstr)), save=False)
        product.save()

        if 'additional_images' in request.FILES:
            for file in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(product=product, image=file)

        if 'additional_cropped_images[]' in request.POST:
            for cropped_image_data in request.POST.getlist('additional_cropped_images[]'):
                if cropped_image_data:
                    format, imgstr = cropped_image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    image = ProductImage(product=product)
                    image.image.save(f'product_additional_{product.id}.{ext}', ContentFile(base64.b64decode(imgstr)), save=False)
                    image.save()

        return redirect('admin_products')

    return render(request, 'Admin side/edit_product.html', {'product': product, 'variants': variants, 'categories': categories,'colors':colors})


def add_variant(request,product_id):
    product = get_object_or_404(Product,id=product_id)
    category = product.category

    if request.method == 'POST':
        color = request.POST.get('variant_color')
        price = request.POST.get('variant_price')
        stock = request.POST.get('variant_stock')

        variant = Variant.objects.create(
            color=color,
            price=price,
            stock=stock,
            product=product,
        )
        
        product.product_count = sum(variant.stock for variant in product.variants.all())
        product.save()
       
        extra_cropped_images = request.POST.getlist('additional_cropped_images[]')
        for index, img_data in enumerate(extra_cropped_images):
            if img_data:
                img_data = base64.b64decode(img_data)
                additional_image_name = f'{slugify(color)}_additional_{index}_{int(time.time())}.jpg'
                img = ContentFile(img_data, name=additional_image_name)
                existing_images = ProductImage.objects.filter(variant=variant, image=img)
                if not existing_images.exists():
                    ProductImage.objects.create(variant=variant, image=img)
            else:
                print(f"Empty image data at index {index}")

        
        category.product_count = sum(product.product_count for product in category.products.all())
        category.save()

        return redirect('admin_products')

    return render(request, 'Admin side/add_variant.html',{'colors':colors})


def unlist_variant(request,variant_id):
    variant=get_object_or_404(Variant,id=variant_id)
    if request.method == 'POST':
        variant.is_listed = not variant.is_listed  # Toggle the is_listed flag
        variant.save()
        return redirect('admin_products')
        
    products=Product.objects.all()
    return render(request, 'Admin side/admin_products.html', {'products': products})