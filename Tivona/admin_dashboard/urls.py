from django.urls import path
from admin_dashboard import views

urlpatterns= [
    path('admin_dashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('admin_orders/',views.admin_orders,name='admin_orders'),
    path('change_order_status/<int:order_id>',views.change_order_status,name='change_order_status'),
    path('admin_order_details/<int:order_id>/',views.admin_order_details,name='admin_order_details'),
    path('admin_coupons/',views.admin_coupons,name='admin_coupons'),
    path('add_coupon', views.add_coupon, name='add_coupon'),
    path('edit_coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('coupons_status/<int:coupon_id>/', views.coupon_status, name='coupon_status'),
    path('banners/',views.banners,name='banners'),
    path('admin_profile/',views.admin_profile,name='admin_profile'),
]