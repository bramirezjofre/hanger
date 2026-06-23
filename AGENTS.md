# Repository Guidelines

## Project Structure & Module Organization

Python application code lives in `src/hanger_app/`. `__init__.py` owns the Flask factory, `routes.py` handles HTTP, `services.py` contains use cases, and `repositories.py` isolates SQLite. Versioned schema files live in `migrations/`; Jinja templates live in `src/hanger_app/templates/`. `src/hanger.py` and `src/loader.py` are compatibility entry points. Tests live in `tests/`. Agent instructions are stored in `.agents/skills/`, with installed versions recorded in `skills-lock.json`.

## Build, Test, and Development Commands

Create an isolated environment before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Run the main application from the repository root:

```bash
PYTHONPATH=src flask --app hanger:web run --debug
```

Run `flask --app hanger:web process-jobs --limit 100` to process queued deliveries. Use `python3 -m compileall -q src tests` as the minimum syntax check. Add schema changes as a new numbered file in `migrations/`; never rewrite an applied migration.

## Coding Style & Naming Conventions

Use four-space indentation and follow PEP 8. Name functions and variables with `snake_case`, classes with `PascalCase`, and constants with `UPPER_SNAKE_CASE`. Add type hints to public methods and route return values. Keep Flask route handlers small; move reusable behavior into `src/base/`. Prefer `pathlib.Path` and repository-relative paths instead of hard-coded `/workspaces/...` locations. Never interpolate user input into SQL or HTML.

## Testing Guidelines

Add new tests under `tests/`, mirroring the source layout. Name files `test_<module>.py` and test functions `test_<behavior>()`. Run `pytest -q` and the compile check before submitting. Route changes should cover successful requests, invalid form data, and expected status codes.

## Commit & Pull Request Guidelines

History uses short, imperative, title-cased subjects such as `Fix Login Validation` or `Add User Loader`. Keep each commit focused. Pull requests must explain the problem, root cause, user impact, and validation performed. Link relevant issues and include screenshots for changes under `pages/`. Do not mix generated files, credentials, local databases, or unrelated refactors into a PR.
