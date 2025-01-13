from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
import random
from datetime import datetime

from alerts.notifications import send_sms_notification

def send_email_verification(user):
    """
    Sends an email verification link to the user's registered email address.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}"

    # Prepare context for the template
    email_context = {
        "user": user,
        "verification_url": verification_link,
        "year": datetime.now().year,
    }

    # Render the HTML content from your template
    subject = "Verify Your Email Address"
    html_content = render_to_string("emails/email_verification.html", email_context)
    text_content = strip_tags(html_content)  # Plain-text fallback

    # Use EmailMultiAlternatives for multi-part MIME (text + HTML)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,  # Plain-text part
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    # Attach HTML alternative
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
        print(f"Email sent to {user.email}")
    except Exception as e:
        print(f"Error sending email to {user.email}: {e}")

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
