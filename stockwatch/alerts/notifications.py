# alerts/notifications.py
from phonenumber_field.phonenumber import to_python
from twilio.rest import Client
from django.conf import settings
from django.core.mail import send_mail
from firebase_admin import messaging

from users.models import UserDevice
import logging

logger = logging.getLogger(__name__)


def send_push_notification(user, title, body):
    
    # Fetch all device tokens for this user
    device_tokens = UserDevice.objects.filter(user=user).values_list('device_token', flat=True)

    if not device_tokens:
        print(f"No device tokens found for user {user.username}. No notification sent.")
        return

    # Construct a multicast message with FCM
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=list(device_tokens),
    )

    # Send the message
    response = messaging.send_each_for_multicast(message)
    print(f"Sent {response.success_count} messages; Failed {response.failure_count} messages.")

    # Optional: Handle failures (e.g., remove invalid tokens from the database)
    for idx, resp in enumerate(response.responses):
        if not resp.success:
            error_token = message.tokens[idx]
            print(f"Failed to send notification to {error_token}: {resp.exception}")
            # You could remove the invalid token from the database here if needed.


def send_sms_notification(user, message):
    """
    Sends an SMS notification to the user's phone number using Twilio.
    """
    if not user.phone_number:
        logger.warning(f"User {user.username} does not have a phone number.")
        return

    if not user.receive_sms_notifications:
        logger.info(f"User {user.username} has opted out of SMS notifications.")
        return

    # Convert the phone number to E.164 format
    phone_number = to_python(user.phone_number)
    if not phone_number or not phone_number.is_valid():
        logger.error(f"User {user.username} has an invalid phone number: {user.phone_number}")
        return

    # Ensure the phone number is in E.164 format
    e164_phone_number = phone_number.as_e164

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=e164_phone_number,
        )
        logger.info(f"SMS sent to {e164_phone_number}.")
    except Exception as e:
        logger.error(f"Error sending SMS to {e164_phone_number}: {e}")


def send_email_notification(user, subject, message):
    """
    Sends an email notification to the user's registered email address.
    """
    if not user.receive_email_notifications:
        logger.info(f"User {user.username} has opted out of email notifications.")
        return

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        logger.info(f"Email sent to {user.email}.")
    except Exception as e:
        logger.error(f"Error sending email to {user.email}: {e}")

