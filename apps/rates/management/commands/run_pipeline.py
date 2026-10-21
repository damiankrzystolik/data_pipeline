import time
from datetime import date, timedelta

from django.core.management import BaseCommand, CommandError, call_command
from django.db.models import Max

from apps.rates.models import MonthlyRatesStats, RawRatesTable, Rate


class Command(BaseCommand):
    help = 'Uruchamia cały pipeline: extract (bronze) -> transform (silver) -> stats (gold)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Okno catch-up: ile ostatnich dni pobrać i przetworzyć (domyślnie 7)',
        )
        parser.add_argument('--table', type=str, default='A', help='Typ tabeli NBP (A, B lub C)')

    def handle(self, *args, **options):
        days = options['days']
        if days < 1:
            raise CommandError('--days musi być >= 1')

        end = date.today()
        start = end - timedelta(days=days)
        self.stdout.write(f'Pipeline: okno {start} -> {end} ({days} dni)')

        started = time.monotonic()
        steps = [
            (
                'extract',
                lambda: call_command(
                    'backfill_rates',
                    table=options['table'],
                    start=start.isoformat(),
                    end=end.isoformat(),
                    sleep=0,
                    stdout=self.stdout,
                ),
            ),
            (
                'transform',
                lambda: call_command('transform_rates', since=start.isoformat(), stdout=self.stdout),
            ),
            ('stats', lambda: call_command('build_stats', stdout=self.stdout)),
        ]
        for name, step in steps:
            self._run_step(name, step)

        self._print_summary(time.monotonic() - started)

    def _run_step(self, name, step):
        step_started = time.monotonic()
        self.stdout.write(f'[{name}] start')
        try:
            step()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'[{name}] BŁĄD: {exc}'))
            raise CommandError(f'Pipeline przerwany na kroku "{name}"') from exc
        self.stdout.write(self.style.SUCCESS(f'[{name}] ok ({time.monotonic() - step_started:.1f}s)'))

    def _print_summary(self, elapsed):
        latest = RawRatesTable.objects.aggregate(latest=Max('effective_date'))['latest']
        self.stdout.write(
            self.style.SUCCESS(
                f'Pipeline zakończony w {elapsed:.1f}s | najnowsza tabela: {latest or "brak"} | '
                f'bronze: {RawRatesTable.objects.count()}, silver: {Rate.objects.count()}, '
                f'gold: {MonthlyRatesStats.objects.count()}'
            )
        )
