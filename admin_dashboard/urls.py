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
    path('approve-refund/<int:order_id>/', views.approve_refund, name='approve_refund'),
    path('admin_offers/', views.admin_offers, name='admin_offers'),
    path('add_category_offer/', views.add_category_offer, name='add_category_offer'),
    path('add_product_offer/', views.add_product_offer, name='add_product_offer'),
    path('get-variants/<int:product_id>/', views.get_variants, name='get_variants'),
    path('change_category_offer_status/<int:offer_id>/',views.change_category_offer_status,name='change_category_offer_status'),
    path('change_product_offer_status/<int:offer_id>/',views.change_product_offer_status,name='change_product_offer_status'),
    path('edit_category_offer/<int:offer_id>/',views.edit_category_offer,name='edit_category_offer'),
    path('edit_product_offer/<int:offer_id>/',views.edit_product_offer,name='edit_product_offer'),
    path('banners/',views.banners,name='banners'),
    path('report/',views.report,name='report'),
    path('admin_profile/',views.admin_profile,name='admin_profile'),
]