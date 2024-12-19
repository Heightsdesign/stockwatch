from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from .serializers import UserProfileSerializer, CountrySerializer, UserDeviceSerializer
from .models import CustomUser, Country, UserDevice
from rest_framework.permissions import IsAuthenticated


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