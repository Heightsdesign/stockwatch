# users/management/commands/clear_table.py

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

class Command(BaseCommand):
    help = 'Clears all records from a specified model/table.'

    def add_arguments(self, parser):
        parser.add_argument('app_label', type=str, help='The app label of the model.')
        parser.add_argument('model_name', type=str, help='The name of the model to clear.')

    def handle(self, *args, **options):
        app_label = options['app_label']
        model_name = options['model_name']

        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            raise CommandError(f"Model '{model_name}' not found in app '{app_label}'.")

        count, _ = model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {count} records from '{app_label}.{model_name}'."))

