from django.db.models import Avg
from .models import Rate
from datetime import timedelta
from django.utils import timezone


def get_recent_rates(code, days=30):
    date_from = timezone.now().date() - timedelta(days=days)
    return Rate.objects.filter(currency_code=code, date__gte=date_from)

def get_average_rates(code, days=30) :
    date_from = timezone.now().date() - timedelta(days=days)
    return Rate.objects.filter(currency_code=code, date__gte=date_from).aggregate(Avg('mid'))['mid__avg']