from django.core.management.base import BaseCommand
from django.db.models import Avg, Min, StdDev, Max
from django.db.models.functions import TruncMonth

from apps.rates.models import MonthlyRatesStats, Rate


class Command(BaseCommand):
    help = 'Build stats for all currencies'

    def handle(self, *args, **options):

        stats = (Rate.objects
                 .annotate(month=TruncMonth('date'))
                 .values('currency_code','month')
                 .annotate(avg_mid=Avg('mid'), min_mid=Min('mid'), max_mid=Max('mid'), stddev_mid=StdDev('mid'))
               )

        objs = [MonthlyRatesStats(**row) for row in stats]
        MonthlyRatesStats.objects.bulk_create(objs, update_conflicts=True, unique_fields=['currency_code', 'month'], update_fields=['avg_mid', 'min_mid', 'max_mid', 'stddev_mid'])

        self.stdout.write(self.style.SUCCESS(f'✓ Build stats for {len(objs)} rows'))