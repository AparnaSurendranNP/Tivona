from django.shortcuts import render,redirect
from wishlist.models import Wishlist,WishlistItem
from categories.models import Category
from products.models import Variant
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.decorators.cache import never_cache

# Create your views here.

@never_cache
def wishlist(request):
    user= request.user
    wishlist = Wishlist.objects.filter(user=user).first()
    wishlistItems=WishlistItem.objects.filter(wishlist=wishlist)
    categories=Category.objects.all()
    context={
        'categories':categories,
        'wishlistItems':wishlistItems,
    }
    return render(request,'User side/wishlist.html',context)

@never_cache
def add_wishlist(request,variant_id): 
    if request.method == 'GET':
        print("Received request to add to wishlist")
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

@never_cache
def remove_wishlistItem(request,wishlistItem_id):
    user=request.user
    if request.method == 'POST':
        wishlist = Wishlist.objects.filter(user=user).first()
        wishlist_item = get_object_or_404(WishlistItem, wishlist=wishlist, pk=wishlistItem_id)
        wishlist_item.delete()
        return redirect('wishlist')
    return redirect('wishlist')