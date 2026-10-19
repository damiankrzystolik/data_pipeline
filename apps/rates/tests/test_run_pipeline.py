from datetime import date, timedelta

import pytest
from django.core.management import CommandError, call_command

from apps.rates.models import MonthlyRatesStats, RawRatesTable, Rate
from apps.rates.tests.factories import RawRatesTableFactory, make_payload

pytestmark = pytest.mark.django_db

BACKFILL_FETCH = "apps.rates.management.commands.backfill_rates.fetch_table_range"


@pytest.fixture
def mock_fetch(mocker):
    return mocker.patch(BACKFILL_FETCH, return_value=[])


class TestRunPipelineOrchestration:
    def test_steps_run_in_order(self, mocker):
        mock_call = mocker.patch("apps.rates.management.commands.run_pipeline.call_command")

        call_command("run_pipeline")

        assert [c.args[0] for c in mock_call.call_args_list] == ["backfill_rates", "transform_rates", "build_stats"]

    def test_window_is_passed_to_extract_and_transform(self, mocker):
        mock_call = mocker.patch("apps.rates.management.commands.run_pipeline.call_command")
        today = date.today()

        call_command("run_pipeline", days=10)

        extract, transform, _ = mock_call.call_args_list
        assert extract.kwargs["start"] == (today - timedelta(days=10)).isoformat()
        assert extract.kwargs["end"] == today.isoformat()
        assert transform.kwargs["since"] == (today - timedelta(days=10)).isoformat()

    def test_failure_stops_pipeline_with_command_error(self, mocker):
        def fake_call(name, *args, **kwargs):
            if name == "transform_rates":
                raise RuntimeError("boom")

        mock_call = mocker.patch(
            "apps.rates.management.commands.run_pipeline.call_command", side_effect=fake_call
        )

        with pytest.raises(CommandError, match="transform"):
            call_command("run_pipeline")

        called = [c.args[0] for c in mock_call.call_args_list]
        assert called == ["backfill_rates", "transform_rates"]  # build_stats nie uruchomiony

    def test_invalid_days_rejected(self):
        with pytest.raises(CommandError):
            call_command("run_pipeline", days=0)


class TestRunPipelineEndToEnd:
    def payloads(self):
        today = date.today()
        return [
            make_payload(today - timedelta(days=2), "1/A/NBP/2026"),
            make_payload(today - timedelta(days=1), "2/A/NBP/2026"),
        ]

    def test_fills_all_layers(self, mock_fetch):
        mock_fetch.return_value = self.payloads()

        call_command("run_pipeline")

        assert RawRatesTable.objects.count() == 2
        assert Rate.objects.count() == 4  # 2 dni x (USD, EUR)
        assert MonthlyRatesStats.objects.filter(currency_code="USD").exists()

    def test_second_run_changes_nothing(self, mock_fetch):
        mock_fetch.return_value = self.payloads()

        call_command("run_pipeline")
        counts = (RawRatesTable.objects.count(), Rate.objects.count(), MonthlyRatesStats.objects.count())
        call_command("run_pipeline")

        assert (RawRatesTable.objects.count(), Rate.objects.count(), MonthlyRatesStats.objects.count()) == counts

    def test_day_without_publication_is_not_an_error(self, mock_fetch, capsys):
        mock_fetch.return_value = []  # weekend / święto: NBP zwraca 404 -> []

        call_command("run_pipeline")

        assert RawRatesTable.objects.count() == 0
        assert "Pipeline zakończony" in capsys.readouterr().out

    def test_catch_up_fills_missed_days(self, mock_fetch):
        today = date.today()
        # wczorajsza tabela już jest, brakujące dni dociąga okno catch-up
        RawRatesTableFactory(effective_date=today - timedelta(days=1), table_no="2/A/NBP/2026")
        mock_fetch.return_value = self.payloads()

        call_command("run_pipeline")

        assert RawRatesTable.objects.count() == 2

    def test_transform_only_touches_the_window(self, mock_fetch):
        old = date.today() - timedelta(days=100)
        RawRatesTableFactory(effective_date=old, table_no="old/A/NBP/2026")
        mock_fetch.return_value = []

        call_command("run_pipeline", days=7)

        assert not Rate.objects.filter(date=old).exists()  # stare dane poza oknem nie są przetwarzane
