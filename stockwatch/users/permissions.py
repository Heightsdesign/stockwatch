# users/permissions.py

from rest_framework.permissions import BasePermission

class IsEmailVerified(BasePermission):
    """
    Allows access only to users with verified email.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_email_verified
        )

class IsPhoneVerified(BasePermission):
    """
    Allows access only to users with verified phone number.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_phone_verified
        )

class IsEmailAndPhoneVerified(BasePermission):
    """
    Allows access only to users with both verified email and phone number.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_email_verified and
            request.user.is_phone_verified
        )
