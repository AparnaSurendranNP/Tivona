from django.urls import path
from admin_user_management import views

urlpatterns= [
    path('admin_users/', views.admin_users, name='admin_view_users'),
   path('block_user/<int:pk>/', views.block_user, name='block_user'),
]