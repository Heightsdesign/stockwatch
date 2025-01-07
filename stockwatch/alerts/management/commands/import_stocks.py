# alerts/management/commands/import_stocks.py

from django.core.management.base import BaseCommand
import csv
from alerts.models import Stock

class Command(BaseCommand):
    help = 'Imports stocks (or other assets) from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('stocks.csv', type=str, help='Path to the CSV file.')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['stocks.csv']
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                symbol = row['symbol']
                name = row['name']
                sector = row.get('sector', '')      # Provide default '' if not present
                asset_type = row.get('asset_type', '')

                # If you prefer blank over None:
                #   if not sector: sector = ''
                #   if not asset_type: asset_type = ''

                stock, created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'name': name,
                        'sector': sector,
                        'asset_type': asset_type,
                    }
                )

                if not created:
                    # The record already exists, so let's update if needed
                    # For example, update name, sector, asset_type if CSV changed
                    updated_fields = []
                    if stock.name != name:
                        stock.name = name
                        updated_fields.append('name')
                    if stock.sector != sector:
                        stock.sector = sector
                        updated_fields.append('sector')
                    if stock.asset_type != asset_type:
                        stock.asset_type = asset_type
                        updated_fields.append('asset_type')

                    if updated_fields:
                        stock.save(update_fields=updated_fields)
                        self.stdout.write(
                            self.style.WARNING(
                                f'Stock {symbol} updated fields: {updated_fields}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Stock {symbol} already exists (no changes).'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Stock {symbol} - {name} created (Sector: {sector}, Type: {asset_type}).'
                        )
                    )
