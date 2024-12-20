from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
import random

from alerts.notifications import send_sms_notification


def send_email_verification(user):
    """
    Sends an email verification link to the user's registered email address.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}"
    subject = "Verify Your Email Address"
    message = f"Hello {user.username},\n\nPlease verify your email by clicking the link below:\n\n{verification_link}\n\nBest regards,\nStock Watch Team"

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def send_sms_verification(user):
    """
    Sends an SMS with a verification code to the user's phone number.
    """
    if not user.phone_number:
        raise ValueError("User does not have a phone number.")

    verification_code = random.randint(100000, 999999)
    user.phone_verification_code = verification_code
    user.save()

    message = f"Your verification code is: {verification_code}"
    send_sms_notification(user, message)
