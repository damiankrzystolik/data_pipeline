import json
from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.rates.models import MonthlyRatesStats
from apps.rates.selectors import get_currencies, get_monthly_averages
from apps.rates.tests.factories import RateFactory

pytestmark = pytest.mark.django_db


def days_ago(n):
    return timezone.now().date() - timedelta(days=n)


def add_month_stat(code, month, avg):
    return MonthlyRatesStats.objects.create(
        currency_code=code, month=month, avg_mid=Decimal(str(avg)), min_mid=Decimal("1"), max_mid=Decimal("9")
    )


def json_script(response, element_id):
    html = response.content.decode()
    start = html.index(f'id="{element_id}"')
    start = html.index(">", start) + 1
    return json.loads(html[start : html.index("</script>", start)])


class TestMonthlyAveragesSelector:
    def test_returns_last_12_months_ascending(self):
        for i in range(15):
            year, month = divmod(2025 * 12 + i, 12)
            add_month_stat("USD", timezone.datetime(year, month + 1, 1).date(), 4 + i / 10)

        result = get_monthly_averages("USD")

        assert len(result) == 12
        assert [s.month for s in result] == sorted(s.month for s in result)
        assert result[-1].month > result[0].month

    def test_only_requested_currency(self):
        add_month_stat("USD", timezone.now().date().replace(day=1), 4)
        add_month_stat("EUR", timezone.now().date().replace(day=1), 4.3)

        assert [s.currency_code for s in get_monthly_averages("EUR")] == ["EUR"]

    def test_empty_when_no_stats(self):
        assert get_monthly_averages("USD") == []


class TestCurrenciesSelector:
    def test_distinct_and_sorted(self):
        RateFactory(currency_code="USD", date=days_ago(1))
        RateFactory(currency_code="USD", date=days_ago(2))
        RateFactory(currency_code="EUR", currency_name="euro", date=days_ago(1))

        assert [c["currency_code"] for c in get_currencies()] == ["EUR", "USD"]


class TestIndexView:
    def test_lists_currencies_with_links(self, client):
        RateFactory(currency_code="USD", date=days_ago(1))

        response = client.get(reverse("rates:index"))

        assert response.status_code == 200
        assert reverse("rates:detail", args=["USD"]) in response.content.decode()

    def test_empty_database_shows_hint(self, client):
        response = client.get(reverse("rates:index"))

        assert response.status_code == 200
        assert "Brak danych" in response.content.decode()


class TestDetailView:
    def test_returns_200_with_average_and_latest(self, client):
        RateFactory(date=days_ago(2), mid=Decimal("4.0"))
        RateFactory(date=days_ago(1), mid=Decimal("5.0"))

        response = client.get(reverse("rates:detail", args=["USD"]))

        assert response.status_code == 200
        assert response.context["average"] == Decimal("4.5")
        assert response.context["latest"].mid == Decimal("5.0")

    def test_daily_data_is_ascending_and_serializable(self, client):
        RateFactory(date=days_ago(1), mid=Decimal("5.0"))
        RateFactory(date=days_ago(3), mid=Decimal("4.0"))

        response = client.get(reverse("rates:detail", args=["USD"]))

        data = json_script(response, "daily-data")
        assert data["values"] == [4.0, 5.0]
        assert data["labels"] == [days_ago(3).isoformat(), days_ago(1).isoformat()]

    def test_code_is_case_insensitive(self, client):
        RateFactory(date=days_ago(1))

        assert client.get("/rates/usd/").status_code == 200

    def test_unknown_currency_returns_404(self, client):
        assert client.get("/rates/XXX/").status_code == 404

    def test_currency_without_recent_rates_returns_404(self, client):
        RateFactory(date=days_ago(90))

        assert client.get("/rates/USD/").status_code == 404

    def test_monthly_data_marks_current_month(self, client):
        RateFactory(date=days_ago(1))
        this_month = timezone.now().date().replace(day=1)
        add_month_stat("USD", this_month, 4.2)

        response = client.get(reverse("rates:detail", args=["USD"]))

        data = json_script(response, "monthly-data")
        assert data["values"] == [4.2]
        assert data["labels"][0].endswith("(do dziś)")

    def test_works_without_monthly_stats(self, client):
        RateFactory(date=days_ago(1))

        response = client.get(reverse("rates:detail", args=["USD"]))

        assert response.status_code == 200
        assert "build_stats" in response.content.decode()
