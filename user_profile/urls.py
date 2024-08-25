from django.urls import path
from user_profile import views

urlpatterns =[
    path('profile/<int:user_id>',views.profile,name='profile page'),
    path('update_profile/<int:user_id>',views.update_profile,name='update_profile'),
    path('change_password/<int:user_id>',views.change_password,name='change_password'),
    path('address_manage/<int:user_id>',views.address,name='address_manage'),
    path('add_address/<int:user_id>',views.add_address,name='add_address'),
    path('edit_address/<int:address_id>',views.edit_address,name='edit_address'),
    path('delete_address/<int:address_id>',views.delete_address,name='delete_address'),
    path('get_address_details/<str:pin_code>/',views.get_address_details, name='get_address_details'),
    path('order_history/',views.order_history,name='order_history'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order_cancel/<int:order_id>/',views.order_cancel,name='order_cancel'),
    path('wallet_details/',views.wallet_details,name='wallet_details'),
    path('wallet_transactions/',views.wallet_transactions,name='wallet_transactions')
    

]