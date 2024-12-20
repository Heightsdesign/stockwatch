from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        try:
            user = CustomUser.objects.get(email=username)
        except CustomUser.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None
