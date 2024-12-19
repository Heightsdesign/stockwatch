from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class Country(models.Model):
    name = models.CharField(max_length=100)
    iso_code = models.CharField(max_length=2, unique=True)
    phone_prefix = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.
    Add additional fields as needed.
    """
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    receive_email_notifications = models.BooleanField(default=True)
    receive_sms_notifications = models.BooleanField(default=False)
    receive_push_notifications = models.BooleanField(default=True)
    receive_direct_messages = models.BooleanField(default=True)

    def __str__(self):
        return self.username


class UserDevice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='devices')
    device_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    device_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        unique_together = (('user', 'device_id'),)

    def __str__(self):
        return f"{self.user.username} - {self.device_token}"

