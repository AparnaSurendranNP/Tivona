from django.urls import path
from products import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('products/',views.admin_products,name='admin_products'),
    path('add_product/',views.add_products,name='add_product'),
    path('fetch_variant_images/',views.fetch_variant_images,name='fetch_variant_images'),
    path('<slug:product_slug>/', views.product_detail,name='product_detail'),
    path('unlist_product/<int:product_id>/',views.unlist_product, name='unlist_product'),
    path('edit_product/<int:product_id>/',views.edit_product, name='edit_product'),
    path('add_variant/<int:product_id>/',views.add_variant,name='add_variant'),
    path('unlist_variant/<int:variant_id>/',views.unlist_variant,name='unlist_variant')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)