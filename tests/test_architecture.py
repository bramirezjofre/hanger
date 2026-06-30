import sqlite3
from pathlib import Path

import pytest

from hanger_app import create_app
from hanger_app.config import Settings
from hanger_app.db import Database


def test_production_requires_secrets():
    with pytest.raises(RuntimeError, match="HANGER_SECRET_KEY"):
        Settings.from_env({"HANGER_ENV": "production"})


def test_production_requires_explicit_persistent_storage():
    with pytest.raises(RuntimeError, match="HANGER_DB_PATH"):
        Settings.from_env({"HANGER_ENV": "production", "HANGER_SECRET_KEY": "secret"})


def test_production_requires_explicit_runtime_settings():
    with pytest.raises(RuntimeError, match="HANGER_REQUIRE_INVITATION"):
        Settings.from_env(
            {
                "HANGER_ENV": "production",
                "HANGER_SECRET_KEY": "secret",
                "HANGER_DB_PATH": "/tmp/hanger.sqlite3",
                "HANGER_UPLOAD_DIR": "/tmp/uploads",
                "HANGER_PUBLIC_URL": "https://hanger.example",
            }
        )


def test_invalid_upload_limit_is_rejected():
    with pytest.raises(RuntimeError, match="HANGER_MAX_UPLOAD_BYTES"):
        Settings.from_env({"HANGER_MAX_UPLOAD_BYTES": "0"})


def test_app_factories_do_not_share_services(tmp_path, monkeypatch):
    monkeypatch.setenv("HANGER_ENV", "development")
    first = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "first.db"),
            "UPLOAD_DIR": str(tmp_path / "first-uploads"),
            "AUTO_MIGRATE": True,
        }
    )
    second = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "second.db"),
            "UPLOAD_DIR": str(tmp_path / "second-uploads"),
            "AUTO_MIGRATE": True,
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
    assert applied == 5


def test_operational_cli_commands(app):
    runner = app.test_cli_runner()
    created = runner.invoke(
        args=[
            "create-admin",
            "--username",
            "operator",
            "--password",
            "SecureAdmin1!",
        ]
    )
    assert created.exit_code == 0
    assert app.extensions["hanger"]["users"].get("operator").role == "admin"

    changed = runner.invoke(args=["set-role", "operator", "user"])
    assert changed.exit_code == 0
    assert app.extensions["hanger"]["users"].get("operator").role == "user"
    assert runner.invoke(args=["db-upgrade"]).exit_code == 0
    assert runner.invoke(args=["process-jobs", "--limit", "1"]).exit_code == 0


def test_installation_settings_defaults_and_cli(app):
    services = app.extensions["hanger"]
    settings = services["installation_settings"]

    site_name = settings.get("branding.site_name")
    assert site_name is not None
    assert site_name.value == "Hanger"
    assert site_name.is_public

    runner = app.test_cli_runner()
    listed = runner.invoke(args=["settings-list", "--public-only"])
    assert listed.exit_code == 0
    assert "branding.site_name" in listed.output
    assert "eligibility.minimum_age" not in listed.output

    updated = runner.invoke(args=["settings-set", "eligibility.minimum_age", "21"])
    assert updated.exit_code == 0
    assert settings.get("eligibility.minimum_age").value == 21

    rejected = runner.invoke(args=["settings-set", "eligibility.minimum_age", "0"])
    assert rejected.exit_code != 0
    assert "integer from 1 to 130" in rejected.output


def test_v2_migration_preserves_valid_social_data(tmp_path):
    path = tmp_path / "legacy.db"
    migrations = Path(__file__).resolve().parents[1] / "src/hanger_app/migrations"
    connection = sqlite3.connect(path)
    connection.executescript((migrations / "001_initial.sql").read_text())
    connection.execute(
        "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at INTEGER)"
    )
    connection.execute(
        "INSERT INTO schema_migrations VALUES ('001_initial.sql', unixepoch())"
    )
    connection.execute(
        "INSERT INTO users (username, password_hash) VALUES ('alice', 'hash')"
    )
    connection.execute(
        "INSERT INTO users (username, password_hash) VALUES ('bob', 'hash')"
    )
    connection.execute(
        "INSERT INTO messages (sender, receiver, content) VALUES ('alice', 'bob', 'hi')"
    )
    connection.execute(
        """
        INSERT INTO attachments
            (message_id, stored_name, original_name, mime_type, size)
        VALUES (1, 'image.png', 'image.png', 'image/png', 10)
        """
    )
    connection.execute("INSERT INTO posts (author, content) VALUES ('alice', 'post')")
    connection.execute(
        "INSERT INTO comments (post_id, author, content) VALUES (1, 'bob', 'reply')"
    )
    connection.execute("INSERT INTO post_likes (post_id, username) VALUES (1, 'bob')")
    connection.commit()
    connection.close()

    Database(path, migrations).migrate()

    with sqlite3.connect(path) as migrated:
        assert (
            migrated.execute(
                "SELECT role FROM users WHERE username = 'alice'"
            ).fetchone()[0]
            == "user"
        )
        assert migrated.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
        assert migrated.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 1
        assert migrated.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 1
        assert migrated.execute("SELECT COUNT(*) FROM comments").fetchone()[0] == 1
        assert migrated.execute("SELECT COUNT(*) FROM post_likes").fetchone()[0] == 1
