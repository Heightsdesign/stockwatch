import braintree
from django.conf import settings

def get_braintree_gateway():
    environment = braintree.Environment.Sandbox
    if getattr(settings, 'BRAINTREE_ENV', '').lower() == 'production':
        environment = braintree.Environment.Production

    return braintree.BraintreeGateway(
        braintree.Configuration(
            environment=environment,
            merchant_id=settings.BRAINTREE_MERCHANT_ID,
            public_key=settings.BRAINTREE_PUBLIC_KEY,
            private_key=settings.BRAINTREE_PRIVATE_KEY,
        )
    )
