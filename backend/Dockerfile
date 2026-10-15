FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances d'abord pour tirer parti du cache Docker.
COPY pyproject.toml README.md ./
COPY app ./app
# Support PostgreSQL optionnel via --build-arg REPOFLOW_INSTALL_POSTGRES=true
# (l'extra "postgres" embarque psycopg ; SQLite reste le défaut).
ARG REPOFLOW_INSTALL_POSTGRES=false
RUN pip install --upgrade pip && \
    pip install . && \
    if [ "$REPOFLOW_INSTALL_POSTGRES" = "true" ]; then \
      pip install "psycopg[binary]>=3.1"; \
    fi

# Outils de migration et de développement (Alembic).
COPY alembic.ini ./
COPY alembic ./alembic

# Répertoire de données persistantes (base SQLite) + utilisateur non-root.
RUN mkdir -p /data && \
    useradd --create-home --uid 1001 repoflow && \
    chown -R repoflow:repoflow /data /app
ENV REPOFLOW_DATABASE_URL=sqlite+pysqlite:////data/repoflow.db

USER repoflow

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
