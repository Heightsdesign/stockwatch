# alerts/management/commands/import_stocks.py

from django.core.management.base import BaseCommand
import csv
from alerts.models import Stock


class Command(BaseCommand):
    help = 'Imports stocks from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('stocks.csv', type=str, help='The path to the CSV file.')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['stocks.csv']
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                symbol = row['symbol']
                name = row['name']
                stock, created = Stock.objects.get_or_create(symbol=symbol, defaults={'name': name})
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Stock {symbol} - {name} created.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Stock {symbol} already exists.'))
