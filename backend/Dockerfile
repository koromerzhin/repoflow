# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances d'abord pour tirer parti du cache Docker.
COPY pyproject.toml README.md ./
COPY app ./app
# L'extra "postgres" embarque psycopg : une même image sert SQLite et PostgreSQL.
RUN pip install --upgrade pip && pip install ".[postgres]"

# Outils de migration et de développement (Alembic).
COPY alembic.ini ./
COPY alembic ./alembic

# Répertoire de données persistantes (base SQLite).
RUN mkdir -p /data
ENV REPOFLOW_DATABASE_URL=sqlite+pysqlite:////data/repoflow.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
