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

    receive_email_notifications = serializers.BooleanField(default=True)
    receive_push_notifications = serializers.BooleanField(default=True)
    receive_direct_messages = serializers.BooleanField(default=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['email'] = self.validated_data.get('email', '')
        data['receive_email_notifications'] = self.validated_data.get('receive_email_notifications', True)
        data['receive_push_notifications'] = self.validated_data.get('receive_push_notifications', True)
        data['receive_direct_messages'] = self.validated_data.get('receive_direct_messages', True)
        return data

    def save(self, request):
        user = super().save(request)
        user.receive_email_notifications = self.cleaned_data.get('receive_email_notifications')
        user.receive_push_notifications = self.cleaned_data.get('receive_push_notifications')
        user.receive_direct_messages = self.cleaned_data.get('receive_direct_messages')
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):

    country = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'country', 'receive_email_notifications', 'receive_push_notifications', 'receive_sms_notifications']
        read_only_fields = ['username']  # Make username uneditable if desired

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.country = validated_data.get('country', instance.country)
        instance.receive_email_notifications = validated_data.get('receive_email_notifications', instance.receive_email_notifications)
        instance.receive_push_notifications = validated_data.get('receive_push_notifications', instance.receive_push_notifications)
        instance.receive_sms_notifications = validated_data.get('receive_sms_notifications', instance.receive_sms_notifications)
        instance.save()
        return instance

    def validate(self, data):
        country = data.get('country')
        phone_number = data.get('phone_number')

        if country and phone_number:
            # Ensure phone_number starts with the correct prefix
            if not phone_number.startswith(country.phone_prefix):
                # Construct a more explicit message
                # For example: "Wrong phone number format. Your number must start with +44 for United Kingdom."
                msg = (
                    f"Wrong phone number format. Your number must start with "
                    f"{country.phone_prefix} for {country.name}."
                )
                raise serializers.ValidationError({"detail": msg})
        return data


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ['id', 'device_token']