from django.shortcuts import render,redirect
from wishlist.models import Wishlist,WishlistItem
from categories.models import Category
from products.models import Variant
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import Http404
from django.contrib.auth.decorators import login_required

# Create your views here.

@never_cache
@login_required
def wishlist(request):
    try:
        user= request.user
        wishlist = Wishlist.objects.filter(user=user).first()
        wishlistItems=WishlistItem.objects.filter(wishlist=wishlist)
        categories=Category.objects.all()
        context={
            'categories':categories,
            'wishlistItems':wishlistItems,
        }
        return render(request,'User side/wishlist.html',context)
    
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('home page')

@never_cache
@login_required
def add_wishlist(request,variant_id):
    try: 
        if request.method == 'GET':
            variant = get_object_or_404(Variant, id=variant_id)
            wishlist ,created= Wishlist.objects.get_or_create(user=request.user)

            wishlist_items,created = WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                variant=variant,
                product=variant.product,
            )

            wishlist_items.save()
            product=variant.product
            messages.success(request,"Item added to wishlist successfully!")
            return redirect('product_detail',product_slug= product.slug)
        
    except Http404:
        messages.error(request,"Variant not found")
        return redirect('home page')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('home page')

@never_cache
@login_required
def remove_wishlistItem(request,wishlistItem_id):
    try:
        user=request.user
        if request.method == 'POST':
            wishlist = Wishlist.objects.filter(user=user).first()
            wishlist_item = get_object_or_404(WishlistItem, wishlist=wishlist, pk=wishlistItem_id)
            wishlist_item.delete()
            return redirect('wishlist')
        return redirect('wishlist')
    except Http404:
        messages.error(request,"Wishlist item not found")
        return redirect('wishlist')
    except Exception as e:
        # Catch any exception and show an error message
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('wishlist')