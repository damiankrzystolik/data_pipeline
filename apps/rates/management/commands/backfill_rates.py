import time
from datetime import date, timedelta

from django.core.management import BaseCommand, CommandError

from apps.rates.nbp_client import fetch_table_range
from apps.rates.models import RawRatesTable

MAX_DAYS = 93


class Command(BaseCommand):
    help = 'Backfill raw rates tables for a date range (chunks of <= 93 days)'

    def add_arguments(self, parser):
        parser.add_argument('--table', type=str, default='A', help='Typ tabeli (A, B lub C)')
        parser.add_argument('--start', type=str, help='YYYY-MM-DD (domyślnie 365 dni temu)')
        parser.add_argument('--end', type=str, help='YYYY-MM-DD (domyślnie dziś)')
        parser.add_argument('--sleep', type=float, default=0.5, help='Pauza między zapytaniami (s)')

    def handle(self, *args, **options):
        end = date.fromisoformat(options['end']) if options['end'] else date.today()
        start = date.fromisoformat(options['start']) if options['start'] else end - timedelta(days=365)
        if start > end:
            raise CommandError('--start musi być <= --end')

        total_created = total_updated = 0
        chunk_start = start
        while chunk_start <= end:
            chunk_end = min(chunk_start + timedelta(days=MAX_DAYS - 1), end)
            tables = fetch_table_range(options['table'], chunk_start.isoformat(), chunk_end.isoformat())

            created_n = 0
            for data in tables:
                _, created = RawRatesTable.objects.update_or_create(
                    effective_date=date.fromisoformat(data['effectiveDate']),
                    defaults={'table_no': data['no'], 'payload': data},
                )
                created_n += created
            total_created += created_n
            total_updated += len(tables) - created_n

            self.stdout.write(
                f'{chunk_start} → {chunk_end}: {len(tables)} tabel ({created_n} nowych)'
            )
            chunk_start = chunk_end + timedelta(days=1)
            if chunk_start <= end:
                time.sleep(options['sleep'])

        self.stdout.write(self.style.SUCCESS(
            f'Gotowe: dodano {total_created}, zaktualizowano {total_updated}'
        ))
