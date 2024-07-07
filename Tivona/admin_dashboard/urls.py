from django.urls import path
from admin_dashboard import views

urlpatterns= [
    path('admin_dashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('admin_orders/',views.admin_orders,name='admin_orders'),
    path('admin_coupons/',views.admin_coupons,name='admin_coupons'),
    path('banners/',views.banners,name='banners'),
    path('admin_profile/',views.admin_profile,name='admin_profile'),
]