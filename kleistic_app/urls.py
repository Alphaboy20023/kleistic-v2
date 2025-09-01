from django.urls import path
from .views import *
from django.conf.urls.static import static
from kleistic_v2 import settings

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    # products
    path('products/', ProductView.as_view(), name='products'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    # orders
    path('orders/', OrderView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderView.as_view(), name='order-detail'),
    # item orders
    path('item-orders/', ItemOrderView.as_view(), name='itemorder-list'),
    path('item-orders/<int:pk>/', ItemOrderView.as_view(), name='itemorder-detail'),
    # payment
    path('initialize-payments/', InitializePaymentView.as_view(), name='initialize-payment'),
    path('verify-payments/', VerifyPaymentView.as_view(), name='verify-payment'),
    # receipts
    path('generate-receipts/', GenerateReceiptView.as_view(), name = 'receipt')
    ] 
    
    
