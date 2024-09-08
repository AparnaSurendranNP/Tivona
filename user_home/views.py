from django.shortcuts import render,redirect
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
from admin_dashboard.models import ProductOffer
from django.utils import timezone

# Create your views here.

@never_cache
def index(request):
        categories=Category.objects.all()
        products_list=Product.objects.all().order_by('name')

        page_number = request.GET.get('page', 1)  # Default to page 1 if not specified
        paginator = Paginator(products_list, 12)  # Show 12 products per page
        
        # Get the current page object
        page_obj = paginator.get_page(page_number)
        latest_products=Product.objects.all().order_by('-id')[:4]

        context={
            'categories': categories,
            'page_obj': page_obj,
            'latest_products': latest_products,
        }
        return render(request,'User side/index.html',context)

@never_cache
def shop(request):
    try: 
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
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('home page')


def search(request):
    try:
        query = request.GET.get('search')
        products = Product.objects.filter(name__icontains=query)
        product = products.filter(name__iexact=query).first()

        if not query:
            messages.error(request, "Sorry, No search query provided")
            return redirect('shop page')
        
        if len(query) == 1 or len(query) == 2:
            messages.error(request, "Sorry, Product not found")
            return redirect('shop page')

        if not products.exists():
            messages.error(request, "Sorry, Product not found")
            return redirect('shop page')

        variant_data = []
        
        if product:
            variants = product.variants.all().select_related('product').prefetch_related('images')
            
            # Check if the product has an offer applied
            if product.offer_applied:
                try:
                    offers = ProductOffer.objects.filter(product=product, valid_from__lte=timezone.now(), valid_to__gte=timezone.now(), is_active=True)
        
                    # Create a dictionary to track the offer details for each variant
                    offer_dict = {offer.variant.id: offer for offer in offers}

                    for variant in variants:
                        offer = offer_dict.get(variant.id)  # Get the offer for the current variant
                        if offer:
                            original_price = variant.price
                            discounted_price = variant.discounted_price
                            variant_data.append({
                                'offer': offer,
                                'variant': variant,
                                'original_price': original_price,
                                'discounted_price': discounted_price,
                                'discount_percentage': offer.discount_percentage
                            })
                        else:
                            variant_data.append({
                                'variant': variant,
                                'original_price': variant.price,
                                'discounted_price': None,
                                'discount_percentage': None
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
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('home page')



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
    try:
        categories = Category.objects.all()
        latest_products = Product.objects.all().order_by('-id')

        offer_option = request.GET.get('offer', 'product_offer')
        sort_option = request.GET.get('sort', 'name')
        current_date = now()

        offered_variants = []

        if offer_option == 'product_offer':
            offers = ProductOffer.objects.filter(valid_from__lte=current_date,valid_to__gte=current_date, is_active=True)
            for offer in offers:
                product = offer.product
                variant = offer.variant
                discount_percentage = offer.discount_percentage
                original_price = variant.price
                discounted_price = original_price - (original_price * discount_percentage / 100)
                variant.discounted_price = discounted_price
                variant.save()

                offered_variants.append({
                    'product': product,
                    'variant': variant,
                    'discount_percentage': discount_percentage
                })

        else:
            messages.error(request, "Sorry, something went wrong")
            return redirect('offers')

        # Sort offered variants if sort_option is provided
        if sort_option and offered_variants:
            offered_variants = sorted(offered_variants, key=lambda x: getattr(x['product'], sort_option))

        # Pagination
        paginator = Paginator(offered_variants, 10)  # Show 10 variants per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'categories': categories,
            'offered_variants': page_obj,
            'offer_option': offer_option,
            'sort_option': sort_option,
            'latest_products': latest_products,
        }

        return render(request, 'User side/offers.html', context)
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('home page')
