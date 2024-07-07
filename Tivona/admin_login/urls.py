from django.urls import path
from admin_login import views

urlpatterns= [
    path('admin_login/',views.admin_login,name='admin_login'),
    path('logout/',views.logout,name='logout')
]