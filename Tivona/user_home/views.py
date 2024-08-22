from django.shortcuts import render,redirect
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from categories.models import Category
from products.models import Product,Variant
from shop_cart.models import Cart,CartItem
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Min
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.contrib import messages
from admin_dashboard.models import CategoryOffer, ProductOffer

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
    elif sort_option == '-name':
        products=products.order_by('-name')
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

    variant_data = []
    
    if product:
        variants = product.variants.all().select_related('product').prefetch_related('images')
        
        # Check if the product has an offer applied
        if product.offer_applied:
            try:
                offer = ProductOffer.objects.get(product=product)
                discount_percentage = offer.discount_percentage
                
                for variant in variants:
                    original_price = variant.price
                    discounted_price = original_price - (original_price * discount_percentage / 100)
                    variant_data.append({
                        'variant': variant,
                        'images': variant.images.all(),
                        'color': variant.color,
                        'original_price': original_price,
                        'discounted_price': discounted_price,
                        'discount_percentage': discount_percentage,
                    })
            except ProductOffer.DoesNotExist:
                # Handle the case where the offer does not exist
                for variant in variants:
                    variant_data.append({
                        'variant': variant,
                        'images': variant.images.all(),
                        'color': variant.color,
                        'original_price': variant.price,
                        'discounted_price': None,
                        'discount_percentage': None,
                    })
        else:
            for variant in variants:
                variant_data.append({
                    'variant': variant,
                    'images': variant.images.all(),
                    'color': variant.color,
                    'original_price': variant.price,
                    'discounted_price': None,
                    'discount_percentage': None,
                })

        suggestions = products.exclude(id=product.id)
    else:
        suggestions = products

    context = {
        'product': product,
        'variant_data': variant_data,
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


@never_cache
def offers(request):
    categories = Category.objects.all()
    latest_products = Product.objects.all().order_by('-id')

    offer_option = request.GET.get('offer', 'product_offer')
    sort_option = request.GET.get('sort', 'name')
    current_date = now()

    offered_products = []

    if offer_option == 'category_offer':
        offers = CategoryOffer.objects.filter(valid_from__lte=current_date, valid_to__gte=current_date, is_active=True)
        category_offer_ids = offers.values_list('category_id', flat=True)
        offered_products = Product.objects.filter(category_id__in=category_offer_ids)

        for product in offered_products:
            category_offer = offers.filter(category=product.category).first()
            if category_offer:
                discount_percentage = category_offer.discount_percentage
                for variant in product.variants.all():
                    original_price = variant.price
                    discounted_price = original_price - (original_price * discount_percentage / 100)
                    variant.discounted_price = discounted_price
                    variant.save()

    elif offer_option == 'product_offer':
        offers = ProductOffer.objects.filter(valid_from__lte=current_date, valid_to__gte=current_date, is_active=True)
        for offer in offers:
            product = offer.product
            variant = offer.variant
            discount_percentage = offer.discount_percentage
            original_price = variant.price
            discounted_price = original_price - (original_price * discount_percentage / 100)
            variant.discounted_price = discounted_price
            variant.save()

            offered_products.append(product)  # Collect the offered products

    else:
        messages.error(request, "Sorry, something went wrong")
        return redirect('offers')

    # Sort offered products if sort_option is provided and offered_products is not empty
    if sort_option and offered_products:
        offered_products = sorted(offered_products, key=lambda x: getattr(x, sort_option))

    # Pagination
    paginator = Paginator(offered_products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'offered_products': page_obj,
        'offer_option': offer_option,
        'sort_option': sort_option,
        'latest_products': latest_products,
    }

    return render(request, 'User side/offers.html', context)
