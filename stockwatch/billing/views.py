# billing/views.py
import braintree
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from braintree.exceptions.braintree_error import BraintreeError  # Updated import
from .braintree_config import get_braintree_gateway


class BraintreeClientTokenView(APIView):
    def get(self, request):
        gateway = get_braintree_gateway()
        try:
            client_token = gateway.client_token.generate({})
            return Response({'client_token': client_token})
        except BraintreeError as e:
            # Something specifically in Braintree's side
            return Response({'detail': str(e)}, status=400)
        except Exception as e:
            # Catch-all if you want to be extra safe
            return Response({'detail': str(e)}, status=400)


class BraintreeCheckoutView(APIView):
    def post(self, request):
        gateway = get_braintree_gateway()
        amount = request.data.get('amount')
        payment_method_nonce = request.data.get('payment_method_nonce')

        if not amount or not payment_method_nonce:
            return Response({'detail': 'Missing amount or payment_method_nonce'}, status=400)

        result = gateway.transaction.sale({
            'amount': str(amount),
            'payment_method_nonce': payment_method_nonce,
            'options': {
                'submit_for_settlement': True
            }
        })

        if result.is_success:
            return Response({
                'transaction_id': result.transaction.id,
                'detail': 'Payment successful!'
            })
        else:
            return Response({
                'detail': result.message,
                'errors': getattr(result, 'errors', None)
            }, status=400)


class BraintreeSubscribeView(APIView):
    def post(self, request):
        plan_id = request.data.get('plan_id')
        payment_method_nonce = request.data.get('payment_method_nonce')

        if not (plan_id and payment_method_nonce):
            return Response({'detail': 'Missing plan_id or payment_method_nonce'}, status=status.HTTP_400_BAD_REQUEST)

        # First create a payment method
        # Option A: create a Vaulted payment method by creating a customer
        # or re-use existing Braintree customer if you store user.braintree_customer_id
        result_customer = braintree.Customer.create({
            'payment_method_nonce': payment_method_nonce,
            # 'email': request.user.email, # optionally store email
        })

        if not result_customer.is_success:
            return Response({'detail': result_customer.message}, status=status.HTTP_400_BAD_REQUEST)

        # We'll get a token for the payment method
        payment_token = result_customer.customer.payment_methods[0].token

        # Now create a subscription with that payment method token
        result_sub = braintree.Subscription.create({
            'plan_id': plan_id,
            'payment_method_token': payment_token
        })

        if result_sub.is_success:
            # store subscription details
            # e.g. user.subscription_plan = local DB plan
            # user.save()
            return Response({'subscription_id': result_sub.subscription.id})
        else:
            return Response({'detail': result_sub.message}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def braintree_webhook(request):
    bt_signature = request.POST.get('bt_signature')
    bt_payload = request.POST.get('bt_payload')

    if not (bt_signature and bt_payload):
        return Response(status=400)

    # parse the webhook
    webhook_notification = braintree.WebhookNotification.parse(
        bt_signature, bt_payload
    )

    if webhook_notification.kind == braintree.WebhookNotification.Kind.SubscriptionCanceled:
        subscription = webhook_notification.subscription
        # find user by subscription.id in your DB
        # set them to 'tier0' or free plan, etc.

    # handle other events
    return Response(status=200)