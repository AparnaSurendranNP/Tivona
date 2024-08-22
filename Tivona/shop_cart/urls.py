from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from shop_cart import views

urlpatterns = [
    path('add_cart/<int:variant_id>',views.add_cart,name='add_cart'),
    path('remove_cart/<int:cartItem_id>',views.remove_cart,name='remove_cart'),
    path('shoping-cart/',views.shoping_cart,name='shoping-cart'),
    path('apply_coupon/',views.apply_coupon,name='apply_coupon'),
    path('remove_coupon/',views.remove_coupon,name='remove_coupon'),
    path('make_order/',views.make_order,name='make_order'),
    path('online_payment_success/',views.online_payment_success,name='online_payment_success'),
    path('place_order/',views.place_order,name='place_order'),
    path('order_success/<int:order_id>/', views.order_success, name='order_success'),
    path('request-refund/<int:order_id>/', views.request_refund, name='request_refund'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)