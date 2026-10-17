from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.rates.selectors import get_average_rates, get_recent_rates
from apps.rates.tests.factories import RateFactory

pytestmark = pytest.mark.django_db


def days_ago(n):
    return timezone.now().date() - timedelta(days=n)


class TestGetRecentRates:
    def test_returns_only_requested_currency(self):
        RateFactory(currency_code="USD", date=days_ago(1))
        RateFactory(currency_code="EUR", date=days_ago(1))

        result = get_recent_rates("USD")

        assert [r.currency_code for r in result] == ["USD"]

    def test_excludes_rates_older_than_window(self):
        RateFactory(date=days_ago(5))
        RateFactory(date=days_ago(31))

        assert get_recent_rates("USD", days=30).count() == 1

    def test_boundary_day_is_included(self):
        RateFactory(date=days_ago(30))

        assert get_recent_rates("USD", days=30).count() == 1

    def test_custom_window(self):
        RateFactory(date=days_ago(3))
        RateFactory(date=days_ago(10))

        assert get_recent_rates("USD", days=7).count() == 1

    def test_empty_when_no_data(self):
        assert get_recent_rates("USD").count() == 0


class TestGetAverageRates:
    def test_average_of_window(self):
        RateFactory(date=days_ago(1), mid=Decimal("4.0"))
        RateFactory(date=days_ago(2), mid=Decimal("5.0"))

        assert get_average_rates("USD") == Decimal("4.5")

    def test_ignores_other_currencies_and_old_rates(self):
        RateFactory(date=days_ago(1), mid=Decimal("4.0"))
        RateFactory(currency_code="EUR", date=days_ago(1), mid=Decimal("100"))
        RateFactory(date=days_ago(60), mid=Decimal("100"))

        assert get_average_rates("USD") == Decimal("4.0")

    def test_none_when_no_data(self):
        assert get_average_rates("USD") is None
