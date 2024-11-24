from django.core.management.base import BaseCommand
from users.models import Country
import csv
import os

class Command(BaseCommand):
    help = 'Load country data into the database'

    def handle(self, *args, **options):
        file_path = os.path.join(os.path.dirname(__file__), 'countries.csv')
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            Country.objects.all().delete()  # Optional: Clear existing data
            for row in reader:
                Country.objects.create(
                    name=row['name'],
                    iso_code=row['iso_code'],
                    phone_prefix=row['phone_prefix']
                )
        self.stdout.write(self.style.SUCCESS('Successfully loaded country data.'))
