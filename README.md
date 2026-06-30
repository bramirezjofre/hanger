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
`HANGER_SECRET_KEY`, `HANGER_DB_PATH`, `HANGER_UPLOAD_DIR`,
`HANGER_PUBLIC_URL`, `HANGER_REQUIRE_INVITATION`, and
`HANGER_MAX_UPLOAD_BYTES`. Configure SMTP or Twilio credentials before
processing delivery jobs. SQLite and uploaded files must live on the same
persistent volume; this deployment profile is intended for a single application
host.

```bash
poetry run flask --app hanger_app:create_app db-upgrade
poetry run flask --app hanger_app:create_app create-admin
poetry run flask --app hanger_app:create_app process-jobs --watch
poetry run flask --app hanger_app:create_app settings-list
poetry run flask --app hanger_app:create_app settings-set eligibility.minimum_age 21
poetry run pytest -q
poetry run ruff check src tests
```

Schema changes belong in numbered SQL files under `src/hanger_app/migrations/`.
Development applies them automatically; production must run `db-upgrade` once before web
workers start. Build the included `Dockerfile` for Gunicorn deployment. Health
checks are available at `/health/live` and `/health/ready`.

Per-installation settings are stored in SQLite and managed with the
`settings-list`, `settings-get`, and `settings-set` CLI commands. Supported
settings include `branding.site_name`, `branding.support_contact`,
`branding.logo_url`, `eligibility.minimum_age`,
`eligibility.allowed_contact_kinds`, and `eligibility.application_prompt`.