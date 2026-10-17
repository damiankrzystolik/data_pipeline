from datetime import date
from decimal import Decimal

import factory

from apps.rates.models import RawRatesTable, Rate


def make_payload(effective_date=date(2026, 10, 9), no="196/A/NBP/2026", rates=None):
    """Tabela A w formacie zwracanym przez NBP (jeden element listy)."""
    if rates is None:
        rates = [
            {"currency": "dolar amerykański", "code": "USD", "mid": 3.65},
            {"currency": "euro", "code": "EUR", "mid": 4.27},
        ]
    return {
        "table": "A",
        "no": no,
        "effectiveDate": effective_date.isoformat(),
        "rates": rates,
    }


class RateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rate

    currency_code = "USD"
    currency_name = "dolar amerykański"
    date = factory.LazyFunction(date.today)
    mid = Decimal("4.000000")


class RawRatesTableFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RawRatesTable

    effective_date = date(2026, 10, 9)
    table_no = "196/A/NBP/2026"
    payload = factory.LazyAttribute(lambda o: make_payload(o.effective_date, o.table_no))
