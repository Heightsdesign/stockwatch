from django.urls import path
from .views import CustomAuthToken, UserProfileView, CountryListView,RegisterDeviceTokenView, UserDeviceListView

urlpatterns = [
    path('api-token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('countries/', CountryListView.as_view(), name='country-list'),
    path('register-device-token/', RegisterDeviceTokenView.as_view(), name='register-device-token'),
    path('devices/', UserDeviceListView.as_view(), name='user-devices'),
]
