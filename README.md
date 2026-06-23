# Hanger

Hanger is an interview-gated social application built with Flask. It includes
registration, login, password recovery, persistent invitations, messaging,
posts, validated image uploads, and a retryable delivery queue.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
flask --app hanger:web run --debug
```

Development data is stored under `instance/`. Production requires
`HANGER_SECRET_KEY` and `HANGER_ADMIN_TOKEN`; configure SMTP or Twilio
credentials before processing delivery jobs.

```bash
flask --app hanger:web process-jobs --limit 100
pytest -q
ruff check src tests
```

Schema changes belong in numbered SQL files under `migrations/` and are applied
automatically when the application factory starts.
