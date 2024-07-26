from django.urls import path
from admin_login import views

urlpatterns= [
    path('admin_login/',views.admin_login,name='admin_login'),
    path('admin_logout/',views.admin_logout,name='admin_logout')
]