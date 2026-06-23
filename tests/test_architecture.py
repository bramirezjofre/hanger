import sqlite3

import pytest

from hanger_app import create_app
from hanger_app.config import Settings


def test_production_requires_secrets():
    with pytest.raises(RuntimeError, match="HANGER_SECRET_KEY"):
        Settings.from_env({"HANGER_ENV": "production"})


def test_app_factories_do_not_share_services(tmp_path, monkeypatch):
    monkeypatch.setenv("HANGER_ENV", "development")
    first = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "first.db"),
            "UPLOAD_DIR": str(tmp_path / "first-uploads"),
        }
    )
    second = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "second.db"),
            "UPLOAD_DIR": str(tmp_path / "second-uploads"),
        }
    )

    assert first.extensions["hanger"]["auth"] is not second.extensions["hanger"]["auth"]


def test_migrations_are_idempotent(app):
    database = app.extensions["hanger"]["database"]
    database.migrate()
    database.migrate()

    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        applied = connection.execute(
            "SELECT COUNT(*) FROM schema_migrations"
        ).fetchone()[0]
    assert applied == 1
