from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from .selectors import get_average_rates, get_currencies, get_monthly_averages, get_recent_rates


def rates_index(request):
    return render(request, 'rates/index.html', {'currencies': get_currencies()})


def rate_detail(request, code):
    code = code.upper()
    recent = list(get_recent_rates(code))
    if not recent:
        raise Http404(f'Brak notowań dla waluty {code}')

    current_month = timezone.now().date().replace(day=1)
    monthly = get_monthly_averages(code)

    context = {
        'code': code,
        'currency_name': recent[-1].currency_name,
        'currencies': get_currencies(),
        'average': get_average_rates(code),
        'latest': recent[-1],
        'daily_data': {
            'labels': [rate.date.isoformat() for rate in recent],
            'values': [float(rate.mid) for rate in recent],
        },
        'monthly_data': {
            'labels': [
                f'{stat.month:%Y-%m}' + (' (do dziś)' if stat.month == current_month else '')
                for stat in monthly
            ],
            'values': [float(stat.avg_mid) for stat in monthly],
        },
    }
    return render(request, 'rates/detail.html', context)
