# Hanger

Hanger is an interview-gated social application built with Flask. It includes
registration, login, password recovery, persistent invitations, messaging,
posts, validated image uploads, and a retryable delivery queue.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install poetry==2.2.1
poetry install -E dev
poetry run flask --app hanger_app:create_app run --debug
```

Development data is stored under `instance/`. Production requires
`HANGER_SECRET_KEY`, `HANGER_DB_PATH`, `HANGER_UPLOAD_DIR`, and
`HANGER_PUBLIC_URL`. Configure SMTP or Twilio credentials before processing
delivery jobs. SQLite and uploaded files must live on the same persistent
volume; this deployment profile is intended for a single application host.

```bash
poetry run flask --app hanger_app:create_app db-upgrade
poetry run flask --app hanger_app:create_app create-admin
poetry run flask --app hanger_app:create_app process-jobs --watch
poetry run pytest -q
poetry run ruff check src tests
```

Schema changes belong in numbered SQL files under `src/hanger_app/migrations/`.
Development applies them automatically; production must run `db-upgrade` once before web
workers start. Build the included `Dockerfile` for Gunicorn deployment. Health
checks are available at `/health/live` and `/health/ready`.
