# Repository Guidelines

## Project Structure & Module Organization

Python application code lives in `src/hanger_app/`. `__init__.py` owns the Flask factory, `routes.py` handles HTTP, `services.py` contains use cases, and `repositories.py` isolates SQLite. Versioned schema files live in `src/hanger_app/migrations/`; Jinja templates live in `src/hanger_app/templates/`. `src/hanger.py` and `src/loader.py` are compatibility entry points. Tests live in `tests/`. Agent instructions are stored in `.agents/skills/`, with installed versions recorded in `skills-lock.json`.

## Build, Test, and Development Commands

Create an isolated environment before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install poetry==2.2.1
poetry install -E dev
```

Run the main application from the repository root:

```bash
poetry run flask --app hanger_app:create_app run --debug
```

Run `poetry run flask --app hanger_app:create_app process-jobs --watch` to process queued deliveries. Use `poetry run python -m compileall -q src tests` as the minimum syntax check. Add schema changes as a new numbered file in `src/hanger_app/migrations/`; never rewrite an applied migration.

## Coding Style & Naming Conventions

Use four-space indentation and follow PEP 8. Name functions and variables with `snake_case`, classes with `PascalCase`, and constants with `UPPER_SNAKE_CASE`. Add type hints to public methods and route return values. Keep Flask route handlers small; move reusable behavior into `src/hanger_app/services.py`. Prefer `pathlib.Path` and repository-relative paths instead of hard-coded locations. Never interpolate user input into SQL or HTML.

## Testing Guidelines

Add new tests under `tests/`, mirroring the source layout. Name files `test_<module>.py` and test functions `test_<behavior>()`. Run `poetry run pytest -q --cov=hanger_app` and the compile check before submitting. Route changes should cover successful requests, authorization failures, invalid data, and expected status codes.

## Commit & Pull Request Guidelines

History uses short, imperative, title-cased subjects such as `Fix Login Validation` or `Add User Loader`. Keep each commit focused. Pull requests must explain the problem, root cause, user impact, and validation performed. Link relevant issues and include screenshots for changes under `pages/`. Do not mix generated files, credentials, local databases, or unrelated refactors into a PR.
