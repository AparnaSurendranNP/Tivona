from django.urls import path
from user_accounts import views

urlpatterns =[
    path('signup/',views.signup,name='signup page'),
    path('send_otp/',views.send_otp,name='otp page'),
    path('login/',views.loginn,name='login page'), 
    path('resend_otp/',views.resend_otp,name='Resend_otp'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('forgot_resend_otp/',views.forgot_resend_otp,name='forgot_resend_otp'),
    path('forgot_otp/', views.forgot_otp, name='forgot_otp'),
    path('set_password/', views.set_password, name='set_password'),
    path('logout/',views.logout,name='logout'),
    
]