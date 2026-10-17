import requests
import json

def fetch_table(table: str, date: str) -> dict | None:
    """
    Pobiera tabele kursów z API NBP

    Args:
        date (str): Data w formacie 'YYYY-MM-DD'
        table (str): Typ tabeli 'a', 'b', 'c'

    Returns:
        dict | None

    Raises:
        RequestException: Problem z siecią
        json.JSONDecodeError: Odpowiedz nie jest JSON
    """

    url = f"https://api.nbp.pl/api/exchangerates/tables/{table}/{date}/"
    # url = 'https://api.nbp.pl/api/exchangerates/tables/a/'
    try:
        response = requests.get(url, timeout=5)
    except requests.Timeout:
        raise requests.exceptions.Timeout(f"Timeout {url} - strona nie odpowiada zbyt długo")

    if response.status_code == 404:
        return None

    if response.status_code != 200:
        raise Exception(f"Problem z API {url} - {response.status_code}")

    data = response.json()
    # print(data[0]['rates'][0:2])
    # print(json.dumps(response.json(), indent=2)) # debug
    return data[0] if data else None

def fetch_table_range(table: str, start: str, end: str) -> list[dict]:
    """
    Pobiera tabele kursów z zakresu dat (maks. 93 dni).

    Returns:
        list[dict]: tabele z zakresu; pusta lista gdy brak notowań (404)
    """
    url = f"https://api.nbp.pl/api/exchangerates/tables/{table}/{start}/{end}/"
    try:
        response = requests.get(url, timeout=15)
    except requests.Timeout:
        raise requests.exceptions.Timeout(f"Timeout {url} - strona nie odpowiada zbyt długo")

    if response.status_code == 404:
        return []

    if response.status_code != 200:
        raise Exception(f"Problem z API {url} - {response.status_code}")

    return response.json()

# fetch_table('a', '2026-10-09')