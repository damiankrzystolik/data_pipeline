from django.core.management import BaseCommand
from apps.rates.nbp_client import fetch_table
from apps.rates.models import RawRatesTable
from datetime import date, datetime

class Command(BaseCommand):
    help = 'Fetches raw rates table'
    def add_arguments(self, parser):
        parser.add_argument('--table', type=str, default='A', help='Typ tabeli (A, B lub C)')
        parser.add_argument('--date', type=str, help='YYYY-MM-DD (domyślnie dziś)')

    def handle(self, *args, **options):
        table_name = options['table']
        requested_date = options['date'] or date.today().isoformat()

        data = fetch_table(table_name, requested_date)

        if data is None:
            self.stdout.write(self.style.ERROR('No data found'))
            return

        raw_table, created = RawRatesTable.objects.update_or_create(
            effective_date=datetime.fromisoformat(data['effectiveDate']).date(),
            defaults={
                'table_no': data['no'],
                'payload': data,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Successfully dodano'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully zaktualizowano'))