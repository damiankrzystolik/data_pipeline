.PHONY: install run migrate test test-fast lint lint-fix security shell ci lock \
        docker-build docker-up docker-down docker-logs docker-migrate \
        docker-migrate-check docker-collectstatic docker-createsuperuser \
        docker-shell docker-test docker-clean \
        prod-build prod-up prod-deploy prod-down prod-restart prod-logs \
        prod-migrate prod-collectstatic prod-createsuperuser prod-shell \
        prod-ssl prod-ssl-renew prod-cron-install prod-cron-remove

# Wymagania lokalne: python 3.12+, uv (pip install uv), make
# Wymagania na serwerze: git, make, docker (z docker compose v2)
# Instalacja uv na serwerze: curl -LsSf https://astral.sh/uv/install.sh | sh

# ============================================================
# Development — lokalnie bez Dockera
# ============================================================

lock:
	uv pip compile requirements/base.txt --python-version 3.12 --python-platform linux --output-file requirements/base.lock --system-certs
	uv pip compile requirements/development.txt --python-version 3.12 --python-platform linux --output-file requirements/development.lock --system-certs
	uv pip compile requirements/testing.txt --python-version 3.12 --python-platform linux --output-file requirements/testing.lock --system-certs
	python -c "open('requirements/.prod_tmp','w').writelines(l for l in open('requirements/production.txt') if 'uwsgi' not in l.lower())"
	uv pip compile requirements/.prod_tmp --python-version 3.12 --python-platform linux --output-file requirements/production.lock --system-certs
	python -c "import os; os.unlink('requirements/.prod_tmp')"

install:
	uv pip install -r requirements/development.lock
	pre-commit install

run:
	python manage.py runserver

migrate:
	python manage.py makemigrations
	python manage.py migrate

test:
	pytest --cov=apps --cov-report=html -v

test-fast:
	pytest -x -q

lint:
	ruff check .
	ruff format --check .

lint-fix:
	ruff check . --fix
	ruff format .

security:
	bandit -r apps/ -ll
	pip-audit -r requirements/base.txt

shell:
	python manage.py shell_plus

ci: lint test security
	@echo "All CI checks passed!"

# ============================================================
# Docker — lokalny stack (db + web + nginx)
# ============================================================

docker-build:
	docker compose -f docker-compose.local.yml build

docker-up:
	docker compose -f docker-compose.local.yml up -d

docker-down:
	docker compose -f docker-compose.local.yml down

docker-logs:
	docker compose -f docker-compose.local.yml logs -f

docker-migrate:
	docker compose -f docker-compose.local.yml exec web python manage.py makemigrations
	docker compose -f docker-compose.local.yml exec web python manage.py migrate

docker-migrate-check:
	docker compose -f docker-compose.local.yml exec web python manage.py makemigrations --check --dry-run
	docker compose -f docker-compose.local.yml exec web python manage.py migrate --check

docker-collectstatic:
	docker compose -f docker-compose.local.yml exec web python manage.py collectstatic --noinput

docker-createsuperuser:
	docker compose -f docker-compose.local.yml exec web python manage.py createsuperuser

docker-shell:
	docker compose -f docker-compose.local.yml exec web python manage.py shell_plus

docker-test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

docker-clean:
	docker compose -f docker-compose.local.yml down -v --remove-orphans
	docker system prune -f

# ============================================================
# Produkcja — wdrożenie krok po kroku
#
# Pierwsze wdrożenie na serwerze:
#   1. git clone <repo> && cd <repo>
#   2. cp .env.example .env  →  nano .env          # uzupełnij wszystkie zmienne
#   3. make prod-build                              # zbuduj image (uv + lock files)
#   4. make prod-up                                 # uruchom cały stack
#   5. make prod-migrate                            # wykonaj migracje bazy
#   6. make prod-collectstatic                      # skopiuj pliki statyczne
#   7. make prod-createsuperuser                    # utwórz konto admina
#   8. make prod-ssl DOMAIN=example.com EMAIL=admin@example.com
#                                                   # pobierz certyfikat Let's Encrypt
#   9. make prod-logs                               # sprawdź czy wszystko działa
#
# Każda kolejna aktualizacja:
#   git pull && make prod-deploy
# ============================================================

prod-build:
	docker compose -f docker-compose.prod.yml build

prod-up:
	docker compose -f docker-compose.prod.yml up -d

prod-deploy:
	docker compose -f docker-compose.prod.yml build web
	docker compose -f docker-compose.prod.yml up -d --no-deps web
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
	docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
	@echo "Deployed!"

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-restart:
	docker compose -f docker-compose.prod.yml restart web

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

prod-migrate:
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

prod-collectstatic:
	docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

prod-createsuperuser:
	docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

prod-shell:
	docker compose -f docker-compose.prod.yml exec web python manage.py shell

prod-ssl:
	docker compose -f docker-compose.prod.yml run --rm certbot \
		certonly --webroot --webroot-path=/var/www/certbot \
		-d $(DOMAIN) --email $(EMAIL) --agree-tos --non-interactive
	docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

prod-ssl-renew:
	docker compose -f docker-compose.prod.yml run --rm certbot renew --quiet
	docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

prod-cron-install:
	(crontab -l 2>/dev/null; echo "0 3,15 * * * cd $(PWD) && make prod-ssl-renew >> /var/log/certbot-renew.log 2>&1") | crontab -
	@echo "Cron zainstalowany. Sprawdź: crontab -l"

prod-cron-remove:
	crontab -l 2>/dev/null | grep -v "$(PWD).*prod-ssl-renew" | crontab -
	@echo "Cron usunięty."
