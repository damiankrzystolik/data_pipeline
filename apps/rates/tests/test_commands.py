from datetime import date

import pytest
from django.core.management import CommandError, call_command

from apps.rates.models import RawRatesTable, Rate
from apps.rates.tests.factories import RawRatesTableFactory, make_payload

pytestmark = pytest.mark.django_db


class TestFetchRates:
    def test_creates_raw_table(self, mocker):
        mocker.patch("apps.rates.management.commands.fetch_rates.fetch_table", return_value=make_payload())

        call_command("fetch_rates", date="2026-10-09")

        raw = RawRatesTable.objects.get()
        assert raw.effective_date == date(2026, 10, 9)
        assert raw.table_no == "196/A/NBP/2026"
        assert raw.payload["rates"][0]["code"] == "USD"

    def test_second_run_updates_instead_of_duplicating(self, mocker):
        mocker.patch("apps.rates.management.commands.fetch_rates.fetch_table", return_value=make_payload())

        call_command("fetch_rates", date="2026-10-09")
        call_command("fetch_rates", date="2026-10-09")

        assert RawRatesTable.objects.count() == 1

    def test_no_data_saves_nothing(self, mocker, capsys):
        mocker.patch("apps.rates.management.commands.fetch_rates.fetch_table", return_value=None)

        call_command("fetch_rates", date="2026-10-10")

        assert RawRatesTable.objects.count() == 0
        assert "No data found" in capsys.readouterr().out


class TestTransformRates:
    def test_creates_rate_per_currency(self):
        RawRatesTableFactory()

        call_command("transform_rates")

        assert Rate.objects.count() == 2
        usd = Rate.objects.get(currency_code="USD")
        assert usd.date == date(2026, 10, 9)
        assert usd.currency_name == "dolar amerykański"
        assert float(usd.mid) == 3.65

    def test_is_idempotent(self):
        RawRatesTableFactory()

        call_command("transform_rates")
        call_command("transform_rates")

        assert Rate.objects.count() == 2

    def test_updates_changed_value(self):
        raw = RawRatesTableFactory()
        call_command("transform_rates")

        raw.payload["rates"][0]["mid"] = 3.99
        raw.save()
        call_command("transform_rates")

        assert float(Rate.objects.get(currency_code="USD").mid) == 3.99

    def test_date_filter_transforms_only_that_day(self):
        RawRatesTableFactory(effective_date=date(2026, 10, 8))
        RawRatesTableFactory(effective_date=date(2026, 10, 9))

        call_command("transform_rates", date="2026-10-09")

        assert set(Rate.objects.values_list("date", flat=True)) == {date(2026, 10, 9)}

    def test_no_raw_tables_creates_nothing(self):
        call_command("transform_rates")

        assert Rate.objects.count() == 0


class TestBackfillRates:
    @pytest.fixture(autouse=True)
    def no_sleep(self, mocker):
        mocker.patch("apps.rates.management.commands.backfill_rates.time.sleep")

    @pytest.fixture
    def mock_range(self, mocker):
        return mocker.patch("apps.rates.management.commands.backfill_rates.fetch_table_range")

    def test_saves_all_returned_tables(self, mock_range):
        mock_range.return_value = [
            make_payload(date(2026, 10, 8), "195/A/NBP/2026"),
            make_payload(date(2026, 10, 9), "196/A/NBP/2026"),
        ]

        call_command("backfill_rates", start="2026-10-01", end="2026-10-09")

        assert RawRatesTable.objects.count() == 2

    def test_range_up_to_93_days_is_single_request(self, mock_range):
        mock_range.return_value = []

        call_command("backfill_rates", start="2026-01-01", end="2026-04-03")  # 93 dni

        assert mock_range.call_count == 1

    def test_longer_range_is_split_into_chunks(self, mock_range):
        mock_range.return_value = []

        call_command("backfill_rates", start="2026-01-01", end="2026-04-04")  # 94 dni

        assert mock_range.call_count == 2
        first, second = mock_range.call_args_list
        assert first.args[1:] == ("2026-01-01", "2026-04-03")
        assert second.args[1:] == ("2026-04-04", "2026-04-04")

    def test_is_idempotent(self, mock_range):
        mock_range.return_value = [make_payload()]

        call_command("backfill_rates", start="2026-10-01", end="2026-10-09")
        call_command("backfill_rates", start="2026-10-01", end="2026-10-09")

        assert RawRatesTable.objects.count() == 1

    def test_start_after_end_raises(self, mock_range):
        with pytest.raises(CommandError):
            call_command("backfill_rates", start="2026-10-09", end="2026-10-01")

        mock_range.assert_not_called()
