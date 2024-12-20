from rest_framework import serializers
from .models import UserDevice
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import CustomUser
from .models import Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'iso_code', 'phone_prefix']


class CustomUserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'receive_email_notifications',
                  'receive_push_notifications', 'receive_direct_messages')

class CustomRegisterSerializer(RegisterSerializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)

    receive_email_notifications = serializers.BooleanField(default=True)
    receive_push_notifications = serializers.BooleanField(default=True)
    receive_direct_messages = serializers.BooleanField(default=True)

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['email'] = self.validated_data.get('email', '')
        data['username'] = self.validated_data.get('username', '')
        data['receive_email_notifications'] = self.validated_data.get('receive_email_notifications', True)
        data['receive_push_notifications'] = self.validated_data.get('receive_push_notifications', True)
        data['receive_direct_messages'] = self.validated_data.get('receive_direct_messages', True)
        return data

    def save(self, request):
        user = super().save(request)
        user.email = self.cleaned_data.get('email')
        user.username = self.cleaned_data.get('username')
        user.receive_email_notifications = self.cleaned_data.get('receive_email_notifications')
        user.receive_push_notifications = self.cleaned_data.get('receive_push_notifications')
        user.receive_direct_messages = self.cleaned_data.get('receive_direct_messages')
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    country = serializers.SlugRelatedField(
        slug_field='iso_code',
        queryset=Country.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'phone_number',
            'country',
            'receive_email_notifications',
            'receive_sms_notifications',
            'receive_push_notifications',
        ]

    def validate(self, data):
        country = data.get('country', None)
        phone_number = data.get('phone_number', '')

        if country and phone_number:
            if not phone_number.startswith(country.phone_prefix):
                raise serializers.ValidationError(
                    f"Phone number must start with {country.phone_prefix} for {country.name}."
                )
        return data


class UserDeviceSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(required=True)
    device_token = serializers.CharField(required=True)

    class Meta:
        model = UserDevice
        fields = ['id', 'user', 'device_token', 'created_at', 'active', 'device_id']
        read_only_fields = ['id', 'user', 'created_at', 'active']