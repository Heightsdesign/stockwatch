from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.decorators import method_decorator
from django.contrib.auth.tokens import default_token_generator

from rest_framework.permissions import IsAuthenticated, AllowAny
from dj_rest_auth.registration.views import RegisterView
from alerts.notifications import send_email_notification, send_sms_notification

import random
import logging

from .models import CustomUser, Country, UserDevice
from .serializers import (
    UserProfileSerializer,
    CountrySerializer,
    UserDeviceSerializer,
    CustomRegisterSerializer,
    VerifyPhoneSerializer,
    SendPhoneVerificationSerializer
)

logger = logging.getLogger(__name__)


class CustomRegisterView(RegisterView):
    """
    Custom registration view that allows unauthenticated users to register.
    Sends verification email and SMS upon successful registration.
    """
    permission_classes = [AllowAny]
    serializer_class = CustomRegisterSerializer

    def create(self, request, *args, **kwargs):
        logger.debug("CustomRegisterView: Received registration request.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        logger.debug(f"CustomRegisterView: Created user {user.username}.")

        # Send verification email
        verification_link = request.build_absolute_uri(
            reverse('verify-email', kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
        )
        email_subject = "Verify Your Email Address"
        email_message = f"Hi {user.username},\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\nThank you!"
        send_email_notification(user, email_subject, email_message)
        logger.debug(f"CustomRegisterView: Sent verification email to {user.email}.")

        # Generate phone verification code
        verification_code = str(random.randint(100000, 999999))
        user.phone_verification_code = verification_code
        user.save()
        logger.debug(f"CustomRegisterView: Generated phone verification code for {user.phone_number}.")

        # Send verification SMS
        sms_message = f"Hi {user.username}, your verification code is {verification_code}."
        send_sms_notification(user, sms_message)
        logger.debug(f"CustomRegisterView: Sent verification SMS to {user.phone_number}.")

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "detail": "User registered successfully. Please verify your email and phone number.",
                "username": user.username,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # Use email instead of username
        serializer = self.serializer_class(data={
            'username': request.data.get('email'),
            'password': request.data.get('password'),
        }, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class CountryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class RegisterDeviceTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserDeviceSerializer(data=request.data)
        if serializer.is_valid():
            device_id = serializer.validated_data['device_id']
            device_token = serializer.validated_data['device_token']
            user = request.user

            # Try to find an existing record for this user/device_id
            user_device, created = UserDevice.objects.update_or_create(
                user=user,
                device_id=device_id,
                defaults={'device_token': device_token}
            )

            if created:
                return Response({'detail': 'Device token registered successfully.'}, status=201)
            else:
                return Response({'detail': 'Device token updated successfully.'}, status=200)
        return Response(serializer.errors, status=400)


class UserDeviceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        devices = UserDevice.objects.filter(user=user)
        serializer = UserDeviceSerializer(devices, many=True)
        return Response(serializer.data, status=200)


class VerifyEmailView(APIView):

    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(CustomUser, pk=uid)
        except (ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({"error": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.is_email_verified = True
            user.save()
            return Response({"message": "Email successfully verified."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


class VerifyPhoneView(APIView):
    """
    Verifies the user's phone number using the code sent via SMS.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = VerifyPhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']

        user = request.user

        if user.phone_verification_code != code:
            return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_phone_verified = True
        user.phone_verification_code = None  # Clear the code after verification
        user.save()
        return Response({"message": "Phone number successfully verified."}, status=status.HTTP_200_OK)


class ResendEmailVerificationView(APIView):
    """
    Resends the email verification link to the user.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    def post(self, request):
        user = request.user

        if user.is_email_verified:
            return Response({"detail": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate new verification token
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Construct verification link
        verification_link = request.build_absolute_uri(
            reverse('verify-email', kwargs={'uidb64': uidb64, 'token': token})
        )

        # Send verification email
        email_subject = "Verify Your Email Address"
        email_message = f"Hi {user.username},\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\nThank you!"
        send_email_notification(user, email_subject, email_message)
        logger.debug(f"ResendEmailVerificationView: Sent verification email to {user.email}.")

        return Response({"detail": "Verification email resent."}, status=status.HTTP_200_OK)


class ResendPhoneVerificationView(APIView):
    """
    Resends the phone verification code via SMS.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    def post(self, request):
        user = request.user

        if user.is_phone_verified:
            return Response({"detail": "Phone number already verified."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a new verification code
        verification_code = str(random.randint(100000, 999999))
        user.phone_verification_code = verification_code
        user.save()
        logger.debug(f"ResendPhoneVerificationView: Generated new verification code for {user.phone_number}.")

        # Send verification SMS
        sms_message = f"Hi {user.username}, your new verification code is {verification_code}."
        send_sms_notification(user, sms_message)
        logger.debug(f"ResendPhoneVerificationView: Sent verification SMS to {user.phone_number}.")

        return Response({"detail": "Verification code resent via SMS."}, status=status.HTTP_200_OK)