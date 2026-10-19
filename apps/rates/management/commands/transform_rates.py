from django.core.management.base import BaseCommand
from apps.rates.models import RawRatesTable, Rate
from datetime import datetime


class Command(BaseCommand):
    help = 'Transform raw rates to clean silver layer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Transform only specific date (YYYY-MM-DD). If not provided, transform all.'
        )
        parser.add_argument(
            '--since',
            type=str,
            help='Transform raw tables with effective date >= this date (YYYY-MM-DD).'
        )

    def handle(self, *args, **options):
        date_filter = options.get('date')
        since = options.get('since')

        # Get raw tables to transform
        raw_tables = RawRatesTable.objects.all()
        if date_filter:
            raw_tables = raw_tables.filter(effective_date=date_filter)
        if since:
            raw_tables = raw_tables.filter(effective_date__gte=since)

        total_rates = 0

        for raw_table in raw_tables:
            data = raw_table.payload
            effective_date = datetime.fromisoformat(data['effectiveDate']).date()

            # Extract each rate (currency) from JSON
            for rate_data in data['rates']:
                rate, created = Rate.objects.update_or_create(
                    currency_code=rate_data['code'],
                    date=effective_date,
                    defaults={
                        'currency_name': rate_data['currency'],
                        'mid': rate_data['mid'],
                    }
                )
                total_rates += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ Transformed {total_rates} rates')
        )
