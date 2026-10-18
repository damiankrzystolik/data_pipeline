from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction

from apps.rates.models import MonthlyRatesStats
from apps.rates.tests.factories import RateFactory

pytestmark = pytest.mark.django_db


def make_rates(code, year, month, mids):
    """Jedno notowanie dziennie od 1. dnia miesiąca, po jednym na każdą wartość z mids."""
    for day, mid in enumerate(mids, start=1):
        RateFactory(currency_code=code, date=date(year, month, day), mid=Decimal(str(mid)))


class TestBuildStats:
    def test_calculates_avg_min_max_stddev(self):
        make_rates("USD", 2026, 10, [3, 4, 5])

        call_command("build_stats")

        stat = MonthlyRatesStats.objects.get()
        assert float(stat.avg_mid) == pytest.approx(4.0)
        assert float(stat.min_mid) == pytest.approx(3.0)
        assert float(stat.max_mid) == pytest.approx(5.0)
        assert float(stat.stddev_mid) == pytest.approx(0.816497, abs=1e-6)  # odchylenie populacyjne

    def test_month_is_first_day_of_month(self):
        RateFactory(date=date(2026, 10, 17))

        call_command("build_stats")

        assert MonthlyRatesStats.objects.get().month == date(2026, 10, 1)

    def test_groups_by_currency_and_month(self):
        make_rates("USD", 2026, 10, [3, 4])
        make_rates("USD", 2026, 11, [5, 6])
        make_rates("EUR", 2026, 10, [4, 5])

        call_command("build_stats")

        assert MonthlyRatesStats.objects.count() == 3
        usd_nov = MonthlyRatesStats.objects.get(currency_code="USD", month=date(2026, 11, 1))
        assert float(usd_nov.avg_mid) == pytest.approx(5.5)

    def test_single_observation_has_zero_stddev(self):
        RateFactory(date=date(2026, 10, 1), mid=Decimal("4.2"))

        call_command("build_stats")

        stat = MonthlyRatesStats.objects.get()
        assert stat.stddev_mid == 0
        assert float(stat.avg_mid) == pytest.approx(4.2)

    def test_is_idempotent(self):
        make_rates("USD", 2026, 10, [3, 4, 5])

        call_command("build_stats")
        call_command("build_stats")

        assert MonthlyRatesStats.objects.count() == 1

    def test_updates_existing_stats_when_rates_change(self):
        make_rates("USD", 2026, 10, [3, 4, 5])
        call_command("build_stats")

        RateFactory(currency_code="USD", date=date(2026, 10, 10), mid=Decimal("9"))
        call_command("build_stats")

        stat = MonthlyRatesStats.objects.get()
        assert float(stat.avg_mid) == pytest.approx(5.25)
        assert float(stat.max_mid) == pytest.approx(9.0)

    def test_min_avg_max_are_ordered(self):
        make_rates("USD", 2026, 10, [3.61, 3.65, 3.72, 3.58])

        call_command("build_stats")

        stat = MonthlyRatesStats.objects.get()
        assert stat.min_mid <= stat.avg_mid <= stat.max_mid

    def test_no_rates_creates_nothing(self):
        call_command("build_stats")

        assert MonthlyRatesStats.objects.count() == 0


class TestMonthlyRatesStatsModel:
    def test_currency_and_month_must_be_unique(self):
        values = {"avg_mid": 4, "min_mid": 3, "max_mid": 5}
        MonthlyRatesStats.objects.create(currency_code="USD", month=date(2026, 10, 1), **values)

        with pytest.raises(IntegrityError), transaction.atomic():
            MonthlyRatesStats.objects.create(currency_code="USD", month=date(2026, 10, 1), **values)

    def test_same_month_different_currency_is_allowed(self):
        values = {"avg_mid": 4, "min_mid": 3, "max_mid": 5}
        MonthlyRatesStats.objects.create(currency_code="USD", month=date(2026, 10, 1), **values)
        MonthlyRatesStats.objects.create(currency_code="EUR", month=date(2026, 10, 1), **values)

        assert MonthlyRatesStats.objects.count() == 2

    def test_default_ordering_is_by_month(self):
        values = {"avg_mid": 4, "min_mid": 3, "max_mid": 5}
        MonthlyRatesStats.objects.create(currency_code="USD", month=date(2026, 11, 1), **values)
        MonthlyRatesStats.objects.create(currency_code="USD", month=date(2026, 10, 1), **values)

        months = list(MonthlyRatesStats.objects.values_list("month", flat=True))

        assert months == [date(2026, 10, 1), date(2026, 11, 1)]
