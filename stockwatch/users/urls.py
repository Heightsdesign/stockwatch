from django.urls import path
from .views import CustomAuthToken, UserProfileView, CountryListView

urlpatterns = [
    path('api-token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('countries/', CountryListView.as_view(), name='country-list'),
]
