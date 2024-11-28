# alerts/management/commands/load_indicator_definitions.py

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from alerts.models import IndicatorDefinition, IndicatorParameter, IndicatorLine

class Command(BaseCommand):
    help = 'Load indicator definitions from a JSON file into the database'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'indicator_definitions.json')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR('Indicator definitions JSON file not found.'))
            return

        with open(file_path, 'r') as file:
            data = json.load(file)

        for indicator_data in data:
            name = indicator_data['name']
            display_name = indicator_data.get('display_name', name)
            description = indicator_data.get('description', '')

            # Create or update the IndicatorDefinition
            indicator, created = IndicatorDefinition.objects.update_or_create(
                name=name,
                defaults={
                    'display_name': display_name,
                    'description': description
                }
            )

            # Remove existing parameters and lines to avoid duplicates
            indicator.parameters.all().delete()
            indicator.lines.all().delete()

            # Create IndicatorParameters
            for param_data in indicator_data.get('parameters', []):
                IndicatorParameter.objects.create(
                    indicator=indicator,
                    name=param_data['name'],
                    display_name=param_data.get('display_name', param_data['name']),
                    param_type=param_data['param_type'],
                    required=param_data.get('required', True),
                    default_value=str(param_data.get('default_value', '')),
                    choices=param_data.get('choices', None)
                )

            # Create IndicatorLines
            for line_data in indicator_data.get('lines', []):
                IndicatorLine.objects.create(
                    indicator=indicator,
                    name=line_data['name'],
                    display_name=line_data.get('display_name', line_data['name'])
                )

            self.stdout.write(self.style.SUCCESS(f"Loaded indicator: {display_name}"))

        self.stdout.write(self.style.SUCCESS('Indicator definitions have been loaded successfully.'))
