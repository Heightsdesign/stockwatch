from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import get_object_or_404
from .serializers import UserProfileSerializer, CountrySerializer, UserDeviceSerializer, CustomRegisterSerializer
from .models import CustomUser, Country, UserDevice
from rest_framework.permissions import IsAuthenticated, AllowAny
from dj_rest_auth.registration.views import RegisterView
import logging

logger = logging.getLogger(__name__)

class CustomRegisterView(RegisterView):
    """
    Custom registration view that allows unauthenticated users to register.
    """
    permission_classes = [AllowAny]
    serializer_class = CustomRegisterSerializer  # Reference the actual class

    def create(self, request, *args, **kwargs):
        logger.debug("CustomRegisterView: Received registration request.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        logger.debug(f"CustomRegisterView: Created user {user.username}.")
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "detail": "User registered successfully.",
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
    def post(self, request):
        user = request.user
        code = request.data.get("code")
        if not code:
            return Response({"error": "Verification code is required."}, status=status.HTTP_400_BAD_REQUEST)

        if str(user.phone_verification_code) == code:
            user.is_phone_verified = True
            user.phone_verification_code = None  # Clear the code after verification
            user.save()
            return Response({"message": "Phone number successfully verified."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)