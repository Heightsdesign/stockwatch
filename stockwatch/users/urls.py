from django.urls import path
from .views import (
    CustomAuthToken,
    UserProfileView,
    CountryListView,
    RegisterDeviceTokenView,
    UserDeviceListView,
    VerifyEmailView,
    VerifyPhoneView,
    CustomRegisterView
)

urlpatterns = [
    path('api-token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('countries/', CountryListView.as_view(), name='country-list'),
    path('register-device-token/', RegisterDeviceTokenView.as_view(), name='register-device-token'),
    path('devices/', UserDeviceListView.as_view(), name='user-devices'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('verify-phone/', VerifyPhoneView.as_view(), name='verify-phone'),
    path('registration/', CustomRegisterView.as_view(), name='custom-registration'),
]
