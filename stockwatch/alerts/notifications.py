# alerts/notifications.py
from phonenumber_field.phonenumber import to_python
from twilio.rest import Client
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


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

def send_alert_notification(alert, current_value):
    """
    Sends an alert notification to the user via email and SMS if conditions are met.
    """
    user = alert.user
    subject = f"Stock Alert Triggered for {alert.stock.symbol}"
    message = (
        f"Hello {user.username},\n\n"
        f"Your alert for {alert.stock.symbol} has been triggered.\n"
        f"Current Value: {current_value}\n\n"
        "Best regards,\nStock Watch Team"
    )

    # Send Email Notification
    if user.receive_email_notifications and user.email:
        send_email_notification(user, subject, message)

    # Send SMS Notification
    if user.receive_sms_notifications and user.phone_number:
        send_sms_notification(user, message)
