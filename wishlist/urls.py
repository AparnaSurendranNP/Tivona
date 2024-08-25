from django.urls import path
from wishlist import views

urlpatterns = [
    path('wishlist/',views.wishlist,name='wishlist'),
    path('add_wishlist/<int:variant_id>',views.add_wishlist,name='add_wishlist'), 
    path('remove_wishlist/<int:wishlistItem_id>',views.remove_wishlistItem,name='remove_wishlist'),
]