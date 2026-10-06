# ============================================
# Stage 1: Builder — kompiluje uWSGI i deps
# ============================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ARG REQUIREMENTS=production
COPY requirements/ /tmp/requirements/
# uv installs from pinned lock file; uwsgi excluded from lock (no binary wheels) — built from source separately.
RUN uv pip install -r /tmp/requirements/${REQUIREMENTS}.lock
ARG INSTALL_UWSGI=false
RUN if [ "$INSTALL_UWSGI" = "true" ]; then uv pip install "uWSGI>=2.0.24"; fi


# ============================================
# Stage 2: Production
# ============================================
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appgroup . .

RUN chmod +x scripts/wait-for-it.sh && \
    mkdir -p staticfiles media && \
    chown -R appuser:appgroup staticfiles media

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

CMD ["uwsgi", "--ini", "/app/config/uwsgi/uwsgi.ini"]
