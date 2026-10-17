import pytest
import requests

from apps.rates.nbp_client import fetch_table, fetch_table_range
from apps.rates.tests.factories import make_payload


@pytest.fixture
def mock_get(mocker):
    return mocker.patch("apps.rates.nbp_client.requests.get")


def make_response(mocker, status=200, json_data=None):
    response = mocker.Mock()
    response.status_code = status
    response.json.return_value = json_data
    return response


class TestFetchTable:
    def test_returns_first_table_on_200(self, mock_get, mocker):
        payload = make_payload()
        mock_get.return_value = make_response(mocker, 200, [payload])

        assert fetch_table("A", "2026-10-09") == payload

    def test_builds_url_with_table_and_date(self, mock_get, mocker):
        mock_get.return_value = make_response(mocker, 200, [make_payload()])

        fetch_table("A", "2026-10-09")

        url = mock_get.call_args.args[0]
        assert url == "https://api.nbp.pl/api/exchangerates/tables/A/2026-10-09/"

    def test_returns_none_on_404(self, mock_get, mocker):
        mock_get.return_value = make_response(mocker, 404)

        assert fetch_table("A", "2026-10-10") is None

    def test_returns_none_on_empty_list(self, mock_get, mocker):
        mock_get.return_value = make_response(mocker, 200, [])

        assert fetch_table("A", "2026-10-09") is None

    def test_raises_on_server_error(self, mock_get, mocker):
        mock_get.return_value = make_response(mocker, 500)

        with pytest.raises(Exception, match="500"):
            fetch_table("A", "2026-10-09")

    def test_timeout_is_reraised_with_message(self, mock_get):
        mock_get.side_effect = requests.Timeout()

        with pytest.raises(requests.exceptions.Timeout, match="Timeout"):
            fetch_table("A", "2026-10-09")


class TestFetchTableRange:
    def test_returns_list_of_tables(self, mock_get, mocker):
        tables = [make_payload(), make_payload()]
        mock_get.return_value = make_response(mocker, 200, tables)

        assert fetch_table_range("A", "2026-10-01", "2026-10-09") == tables

    def test_builds_url_with_range(self, mock_get, mocker):
        mock_get.return_value = make_response(mocker, 200, [])

        fetch_table_range("A", "2026-10-01", "2026-10-09")

        url = mock_get.call_args.args[0]
        assert url == "https://api.nbp.pl/api/exchangerates/tables/A/2026-10-01/2026-10-09/"

    def test_returns_empty_list_on_404(self, mock_get, mocker):
        mock_get.return_value = make_response(mocker, 404)

        assert fetch_table_range("A", "2026-10-10", "2026-10-11") == []

    def test_raises_on_server_error(self, mock_get, mocker):
        mock_get.return_value = make_response(mocker, 503)

        with pytest.raises(Exception, match="503"):
            fetch_table_range("A", "2026-10-01", "2026-10-09")

    def test_timeout_is_reraised_with_message(self, mock_get):
        mock_get.side_effect = requests.Timeout()

        with pytest.raises(requests.exceptions.Timeout, match="Timeout"):
            fetch_table_range("A", "2026-10-01", "2026-10-09")
