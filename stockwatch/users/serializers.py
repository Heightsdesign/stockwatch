from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
import logging
import random

from alerts.notifications import send_sms_notification
from .models import UserDevice
from .models import CustomUser
from .models import Country

logger = logging.getLogger(__name__)


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
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    receive_email_notifications = serializers.BooleanField(default=True)
    receive_push_notifications = serializers.BooleanField(default=False)
    receive_direct_messages = serializers.BooleanField(default=False)

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_phone_number(self, value):
        """
        Only check uniqueness if the user actually provided a phone number.
        """
        if value:  # if not empty or null
            # Strip whitespace just in case
            cleaned_value = value.strip()
            if CustomUser.objects.filter(phone_number=cleaned_value).exists():
                raise serializers.ValidationError("A user with this phone number already exists.")
            return cleaned_value
        return value

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['email'] = self.validated_data.get('email', '')
        data['username'] = self.validated_data.get('username', '')
        data['phone_number'] = self.validated_data.get('phone_number', '') or None
        data['receive_email_notifications'] = self.validated_data.get('receive_email_notifications', True)
        data['receive_push_notifications'] = self.validated_data.get('receive_push_notifications', False)
        data['receive_direct_messages'] = self.validated_data.get('receive_direct_messages', False)

        return data

    def save(self, request):
        user = super().save(request)
        user.email = self.cleaned_data.get('email')
        user.username = self.cleaned_data.get('username')
        user.phone_number = self.cleaned_data.get('phone_number')
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
            "is_phone_verified",
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

    def update(self, instance, validated_data):
        """
        If user toggles `receive_sms_notifications` from False to True,
        has a non-empty phone number, and is not phone-verified yet,
        generate a new phone verification code and send an SMS.
        """
        old_sms_pref = instance.receive_sms_notifications
        old_phone = instance.phone_number

        # Perform the normal update first
        instance = super().update(instance, validated_data)

        new_sms_pref = instance.receive_sms_notifications
        new_phone = instance.phone_number

        # If toggling from OFF -> ON, phone is present, and not yet verified:
        if (not old_sms_pref) and new_sms_pref and new_phone and not instance.is_phone_verified:
            verification_code = str(random.randint(100000, 999999))
            instance.phone_verification_code = verification_code
            instance.save()  # Make sure the code is stored

            sms_message = f"Hi {instance.username}, your verification code is {verification_code}."
            send_sms_notification(instance, sms_message)

            logger.debug(
                f"UserProfileSerializer.update: "
                f"Sent phone verification code to {instance.phone_number} for user {instance.username}."
            )
        else:
            logger.debug(
                f"UserProfileSerializer.update: No SMS verification triggered. "
                f"(old_sms={old_sms_pref}, new_sms={new_sms_pref}, phone={new_phone}, verified={instance.is_phone_verified})"
            )

        return instance


class UserDeviceSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(required=True)
    device_token = serializers.CharField(required=True)

    class Meta:
        model = UserDevice
        fields = ['id', 'user', 'device_token', 'created_at', 'active', 'device_id']
        read_only_fields = ['id', 'user', 'created_at', 'active']


class SendPhoneVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class VerifyPhoneSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)