# Plan: pipeline kursów walut NBP (Django + Postgres)

Oct 5, 2026 · @Damian

## Cel projektu

Codziennie pobierasz kursy walut z API NBP, zapisujesz je w PostgreSQL w warstwach (surowe → czyste → agregaty) i pokazujesz na wykresie w Django. Całość działa w kontenerach na Twoim serwerze.

Efekt końcowy:

- rok historii kursów \~30 walut w bazie
- automatyczne pobieranie co dzień roboczy, bez duplikatów
- testy jakości danych z zapisem wyników
- strona z wykresem kursu i endpoint JSON

Źródło: [API NBP](https://api.nbp.pl/), darmowe, bez klucza. Przykład: `https://api.nbp.pl/api/exchangerates/tables/A/?format=json`. Jedno zapytanie obejmuje maksymalnie 93 dni.

## Architektura i stack

Dwa kontenery w jednym `docker compose`: Django wykonuje całą logikę pipeline'u jako komendy `manage.py`, a Postgres trzyma dane w warstwach. Cron na hoście uruchamia pipeline raz dziennie.

&#91;embedded content: architektura · 2 kontenery, 4 warstwy danych\]

Stack: Python 3.12, Django 5, PostgreSQL 16, `requests`, `psycopg`, Chart.js z CDN. Bez Celery i Airflow na start, żeby skupić się na danych, nie na narzędziach.

## Model danych

Cztery modele Django w aplikacji `rates`, jedna tabela na warstwę plus log jakości.

| Model | Warstwa | Pola | Klucz / ograniczenie |
| --- | --- | --- | --- |
| `RawRatesTable` | bronze | `effective_date`, `table_no`, `payload` (JSONField), `fetched_at` | `unique(effective_date)` |
| `Rate` | silver | `currency_code`, `currency_name`, `date`, `mid` (Decimal 12,6) | `unique(currency_code, date)`, indeks na `date` |
| `MonthlyRateStats` | gold | `currency_code`, `month`, `avg_mid`, `min_mid`, `max_mid`, `stddev_mid` | `unique(currency_code, month)` |
| `DataQualityCheck` | log | `check_name`, `run_at`, `passed`, `details` (JSON) | — |

Zasada: surowy JSON zostaje nietknięty, więc transformację możesz zawsze odtworzyć od zera bez ponownego pytania API.

## Etapy krok po kroku

Osiem etapów, każdy kończy się czymś, co działa. Szacunki czasu są orientacyjne, dla kogoś, kto zna już podstawy Django.

### 1. Infrastruktura (ok. 1 wieczór)

- [ ] `docker-compose.yml` z usługami `db` (postgres:16) i `web` (Django)
- [ ] wolumen na dane Postgresa, zmienne w pliku `.env` (poza gitem)
- [ ] `psycopg` w `requirements.txt`, `DATABASES` czytane ze zmiennych środowiskowych
- [ ] `docker compose up`, migracje, logowanie do admina działa

### 2. Extract + Load raw (ok. 1 wieczór)

- [ ] aplikacja `rates`, model `RawRatesTable`
- [ ] moduł `rates/nbp_client.py`: funkcja pobierająca tabelę A dla zakresu dat (`requests`, timeout, obsługa 404 = brak notowań w dany dzień)
- [ ] komenda `python manage.py fetch_rates --date RRRR-MM-DD` zapisująca surowy JSON przez `update_or_create`

### 3. Transform (ok. 1 wieczór)

- [ ] model `Rate` z `UniqueConstraint`
- [ ] komenda `transform_rates`: z każdego `RawRatesTable` wyciąga wiersze i robi upsert (`bulk_create(..., update_conflicts=True)`)
- [ ] test: dwukrotne uruchomienie daje tę samą liczbę wierszy (idempotencja)

### 4. Backfill (ok. pół wieczoru)

- [ ] komenda `backfill_rates --start --end` dzieląca zakres na kawałki po ≤ 93 dni
- [ ] krótka pauza między zapytaniami, logowanie postępu
- [ ] załaduj ostatnie 12 miesięcy

### 5. Agregaty (ok. pół wieczoru)

- [ ] model `MonthlyRateStats` lub widok SQL w migracji (`RunSQL`)
- [ ] komenda `build_stats` licząca średnią, min, max i odchylenie per waluta i miesiąc (`TruncMonth` + `Avg`, `Min`, `Max`, `StdDev`)

### 6. Harmonogram (ok. pół wieczoru)

- [ ] komenda zbiorcza `run_pipeline` = fetch → transform → stats → checks
- [ ] cron na serwerze w dni robocze ok. 12:30 (NBP publikuje tabelę A około południa): `docker compose exec -T web python manage.py run_pipeline`
- [ ] logi do pliku lub `docker logs`

### 7. Jakość danych (ok. 1 wieczór)

- [ ] brak nulli w `mid`, `mid > 0`
- [ ] każdy dzień roboczy ma tabelę (święta jako znane wyjątki)
- [ ] zmiana kursu dzień do dnia < 10% (podejrzane skoki)
- [ ] wynik każdego testu zapisany w `DataQualityCheck`, widoczny w adminie

### 8. Prezentacja (ok. 1 wieczór)

- [ ] widok `/rates/<kod>/` z wykresem Chart.js (CDN) i wyborem waluty
- [ ] endpoint `/api/rates/<kod>/?from=&to=` zwracający JSON
- [ ] strona statusu: data ostatniego pobrania i wynik ostatnich testów

## Pierwszy wieczór: od czego zacząć

Cel na dziś to etap 1 i pierwszy ręczny `fetch_rates`. Wtedy w adminie zobaczysz prawdziwe dane z NBP.

1. Sprawdź API w przeglądarce lub `curl`, żeby zobaczyć strukturę JSON-a.
2. Załóż repo i katalog projektu: `docker-compose.yml`, `.env`, `requirements.txt`, `Dockerfile`.
3. Dodaj usługę `db` i podłącz Django do Postgresa.
4. Utwórz aplikację `rates` i model `RawRatesTable`, zrób migrację.
5. Napisz `nbp_client.py` i komendę `fetch_rates` dla dzisiejszej daty.
6. Zarejestruj model w adminie i obejrzyj zapisany JSON.

Szkielet `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16
    env_file: .env
    volumes:
      - pgdata:/var/lib/postgresql/data
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - db
volumes:
  pgdata:
```

Jeśli Django już działa w kontenerze na SQLite, wystarczy dopisać usługę `db` i zmienić `DATABASES`.

## Rozszerzenia na później

Kiedy wszystkie osiem etapów działa, każde z tych rozszerzeń uczy jednej nowej rzeczy:

- **Drugie źródło:** pogoda z Open-Meteo albo jakość powietrza z GIOŚ i łączenie danych po dacie
- **Celery + Redis:** kolejka zadań i Celery Beat zamiast crona
- **Orkiestrator:** Airflow lub Dagster w osobnym kontenerze, pipeline jako DAG
- **dbt:** transformacje silver/gold jako modele SQL z testami
- **Format kolumnowy:** eksport do Parquet i analiza w DuckDB
- **Monitoring:** alert e-mailem lub na Telegram, gdy test jakości nie przejdzie
