# alerts/management/commands/test_send_sms.py

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from alerts.notifications import send_sms_notification

class Command(BaseCommand):
    help = 'Test sending an SMS notification to a specified user.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the user to send SMS to.'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to send SMS to.'
        )
        parser.add_argument(
            '--message',
            type=str,
            default='This is a test SMS from your application!',
            help='Custom message to send via SMS.'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options.get('username')
        email = options.get('email')
        message = options.get('message')

        # Validate input arguments
        if not username and not email:
            raise CommandError('You must provide either --username or --email to identify the user.')

        try:
            if username:
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError('User not found. Please check the provided username/email.')

        # Check if user has a phone number
        if not getattr(user, 'phone_number', None):
            self.stdout.write(self.style.ERROR('The specified user does not have a phone number.'))
            return

        # Send SMS Notification
        self.stdout.write(f"Attempting to send SMS to {user.phone_number}...")
        success = send_sms_notification(user, message)

        if success:
            self.stdout.write(self.style.SUCCESS(f"SMS sent successfully to {user.phone_number}."))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to send SMS to {user.phone_number}. Check logs for details."))
