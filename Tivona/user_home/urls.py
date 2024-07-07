from django.urls import path
from user_home import views

urlpatterns = [
    path('',views.index,name='home page'),
    path('shop/',views.shop,name='shop page'), 
    path('contact/',views.contact,name='contact page'),
]