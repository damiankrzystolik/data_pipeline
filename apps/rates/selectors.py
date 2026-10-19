from datetime import timedelta

from django.db.models import Avg
from django.utils import timezone

from .models import MonthlyRatesStats, Rate


def get_recent_rates(code, days=30):
    date_from = timezone.now().date() - timedelta(days=days)
    return Rate.objects.filter(currency_code=code, date__gte=date_from).order_by('date')


def get_average_rates(code, days=30):
    date_from = timezone.now().date() - timedelta(days=days)
    return Rate.objects.filter(currency_code=code, date__gte=date_from).aggregate(Avg('mid'))['mid__avg']


def get_monthly_averages(code, months=12):
    """Ostatnie `months` wierszy MonthlyRatesStats dla waluty, rosnąco po miesiącu."""
    latest = MonthlyRatesStats.objects.filter(currency_code=code).order_by('-month')[:months]
    return sorted(latest, key=lambda stat: stat.month)


def get_currencies():
    """Dostępne waluty (kod + nazwa), posortowane po kodzie."""
    return (
        Rate.objects.order_by('currency_code')
        .values('currency_code', 'currency_name')
        .distinct()
    )
