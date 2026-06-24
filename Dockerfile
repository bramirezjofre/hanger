FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HANGER_ENV=production \
    HANGER_DB_PATH=/data/hanger.sqlite3 \
    HANGER_UPLOAD_DIR=/data/uploads

WORKDIR /app

RUN python -m pip install --no-cache-dir poetry==2.2.1 \
    && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock README.md LICENSE ./
COPY src ./src
RUN poetry install --only main --no-interaction

RUN mkdir -p /data/uploads
VOLUME ["/data"]
EXPOSE 8000

CMD ["sh", "-c", "flask --app hanger_app:create_app db-upgrade && exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} 'hanger_app:create_app()'"]
