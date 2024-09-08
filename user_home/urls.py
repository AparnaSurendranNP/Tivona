from django.urls import path
from user_home import views

urlpatterns = [
    path('',views.index,name='home page'),
    path('shop/',views.shop,name='shop page'), 
    path('offers/',views.offers,name='offers'), 
    path('contact/',views.contact,name='contact page'),
    path('search/', views.search, name='search'),
    path('suggest-products/', views.suggest_products, name='suggest_products'),
]
