from django.urls import path
from .views import CustomAuthToken, UserProfileView, CountryListView,RegisterDeviceTokenView

urlpatterns = [
    path('api-token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('countries/', CountryListView.as_view(), name='country-list'),
    path('api-register-device-token/', RegisterDeviceTokenView.as_view(), name='register-device-token'),
]
