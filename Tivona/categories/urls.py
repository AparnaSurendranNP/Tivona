from django.urls import path
from categories import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns =[
    path('category/',views.admin_categories,name='admin_categories'),
    path('add_category/',views.add_category,name='add_category'),
    path('<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('unlist_category/<int:category_id>/',views.unlist_category, name='unlist_category'),
    path('edit_category/<int:category_id>/',views.edit_category, name='edit_category'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)