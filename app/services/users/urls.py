from django.urls import path
from . import views


urlpatterns = [
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('confirm_email/', views.ConfirmEmailAndLoginAPIView.as_view(), name='confirm_email'),
    path('generate_new_otp/', views.ConfirmEmailAndLoginAPIView.as_view(), name='confirm_email'),
]
