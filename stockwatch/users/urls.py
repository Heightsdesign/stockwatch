from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomAuthToken,
    UserProfileView,
    CountryListView,
    RegisterDeviceTokenView,
    UserDeviceListView,
    VerifyEmailView,
    VerifyPhoneView,
    CustomRegisterView,
    ResendEmailVerificationView,
    ResendPhoneVerificationView,
    ContactView,
    SubscriptionPlanViewSet
)


router = DefaultRouter()
router.register(r'subscription_plans', SubscriptionPlanViewSet, basename='subscription_plans')

urlpatterns = [
    path('api-token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('countries/', CountryListView.as_view(), name='country-list'),
    path('register-device-token/', RegisterDeviceTokenView.as_view(), name='register-device-token'),
    path('devices/', UserDeviceListView.as_view(), name='user-devices'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('verify-phone/', VerifyPhoneView.as_view(), name='verify-phone'),
    path('registration/', CustomRegisterView.as_view(), name='custom-registration'),
    path('resend-phone-verification/', ResendPhoneVerificationView.as_view(), name='resend-phone-verification'),
    path('resend-email-verification/', ResendEmailVerificationView.as_view(), name='resend-email-verification'),
    path('contact/', ContactView.as_view(), name='contact'),
]
