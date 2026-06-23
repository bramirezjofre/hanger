# Repository Guidelines

## Project Structure & Module Organization

Python application code lives in `src/`. `src/hanger.py` defines the main Flask application, while `src/loader.py` handles interviewer-driven user loading. Shared domain objects and workflows are in `src/base/user.py` and `src/base/interviewer.py`. Static HTML, CSS, and images live under `pages/`; keep generated or user-uploaded content out of version control. Tests live in `tests/` and mirror the source modules. Agent instructions are stored in `.agents/skills/`, with installed versions recorded in `skills-lock.json`.

## Build, Test, and Development Commands

Create an isolated environment before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask pytest ruff
```

Run the main application from the repository root:

```bash
PYTHONPATH=src flask --app hanger:web run --debug
```

Run `PYTHONPATH=src flask --app loader:loads run --debug` for the loader application. Use `python3 -m compileall -q src` as the minimum syntax check. The project has no dependency manifest yet, so document any additional packages required by a change.

## Coding Style & Naming Conventions

Use four-space indentation and follow PEP 8. Name functions and variables with `snake_case`, classes with `PascalCase`, and constants with `UPPER_SNAKE_CASE`. Add type hints to public methods and route return values. Keep Flask route handlers small; move reusable behavior into `src/base/`. Prefer `pathlib.Path` and repository-relative paths instead of hard-coded `/workspaces/...` locations. Never interpolate user input into SQL or HTML.

## Testing Guidelines

Add new tests under `tests/`, mirroring the source layout. Name files `test_<module>.py` and test functions `test_<behavior>()`. Run `pytest -q` and the compile check before submitting. Route changes should cover successful requests, invalid form data, and expected status codes.

## Commit & Pull Request Guidelines

History uses short, imperative, title-cased subjects such as `Fix Login Validation` or `Add User Loader`. Keep each commit focused. Pull requests must explain the problem, root cause, user impact, and validation performed. Link relevant issues and include screenshots for changes under `pages/`. Do not mix generated files, credentials, local databases, or unrelated refactors into a PR.
