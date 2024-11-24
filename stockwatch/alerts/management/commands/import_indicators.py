# alerts/management/commands/import_indicators.py

from django.core.management.base import BaseCommand
import csv
from alerts.models import Indicator, IndicatorLine

class Command(BaseCommand):
    help = 'Imports indicators and their lines from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file.')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                indicator_name = row['indicator_name']
                line_name = row['line_name']

                indicator, created_indicator = Indicator.objects.get_or_create(name=indicator_name)
                if created_indicator:
                    self.stdout.write(self.style.SUCCESS(f"Indicator '{indicator_name}' created."))
                else:
                    self.stdout.write(f"Indicator '{indicator_name}' already exists.")

                line, created_line = IndicatorLine.objects.get_or_create(name=line_name)
                if created_line:
                    self.stdout.write(self.style.SUCCESS(f"  Line '{line_name}' created."))
                else:
                    self.stdout.write(f"  Line '{line_name}' already exists.")

                # Add the line to the indicator's lines if not already present
                if not indicator.lines.filter(pk=line.pk).exists():
                    indicator.lines.add(line)
                    self.stdout.write(self.style.SUCCESS(f"  Line '{line_name}' added to '{indicator_name}'."))
                else:
                    self.stdout.write(f"  Line '{line_name}' already associated with '{indicator_name}'.")
