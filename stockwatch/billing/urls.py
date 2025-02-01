from django.urls import path
from .views import BraintreeClientTokenView, BraintreeCheckoutView

urlpatterns = [
    path('braintree/client_token/', BraintreeClientTokenView.as_view()),
    path('braintree/checkout/', BraintreeCheckoutView.as_view(), name='braintree-checkout'),
]
