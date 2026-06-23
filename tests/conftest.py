import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("HANGER_ENV", "development")
    from hanger_app import create_app

    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_TOKEN": "test-admin",
            "DATABASE_PATH": str(tmp_path / "hanger.sqlite3"),
            "UPLOAD_DIR": str(tmp_path / "uploads"),
            "PUBLIC_URL": "http://test.local",
            "MAX_CONTENT_LENGTH": 1024 * 1024,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf(client):
    client.get("/")
    with client.session_transaction() as current_session:
        return current_session["_csrf_token"]
