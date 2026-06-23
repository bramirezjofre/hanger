import sqlite3

import pytest

from base.interviewer import HangerSteps, loadUser


PASSWORD = "SecurePass1!"
NEW_PASSWORD = "SaferPassword2@"


def test_register_and_login_use_a_password_hash(tmp_path):
    database = tmp_path / "users.db"
    service = HangerSteps(database)

    assert service.register("alice", PASSWORD)
    assert not service.register("alice", PASSWORD)
    assert not service.login("alice", "incorrect")
    assert service.login("alice", PASSWORD)

    with sqlite3.connect(database) as connection:
        stored_password = connection.execute(
            "SELECT password FROM hanger_register WHERE user = ?", ("alice",)
        ).fetchone()[0]
    assert stored_password.startswith("pbkdf2_sha256$")
    assert PASSWORD not in stored_password


def test_sql_metacharacters_are_stored_as_data(tmp_path):
    service = HangerSteps(tmp_path / "users.db")
    username = "alice'); DROP TABLE hanger_register; --"

    assert service.register(username, PASSWORD)
    assert service.login(username, PASSWORD)


def test_password_recovery_token_is_single_use(tmp_path):
    service = HangerSteps(tmp_path / "users.db")
    service.register("alice", PASSWORD)
    token = service.create_password_recovery_token("alice")

    assert token is not None
    assert not service.password_recovery("alice", "invalid-token", NEW_PASSWORD)
    assert service.password_recovery("alice", token, NEW_PASSWORD)
    assert not service.password_recovery("alice", token, PASSWORD)
    assert not service.login("alice", PASSWORD)
    assert service.login("alice", NEW_PASSWORD)


def test_loader_dispatches_supported_contacts(monkeypatch):
    loader = loadUser()
    calls = []
    monkeypatch.setattr(loader, "_send_email", lambda address: calls.append(address))

    assert loader.add_user("email", "person@example.com")
    assert not loader.add_user("email", "person@example.com")
    assert loader.send_steps() == ["person@example.com"]
    assert calls == ["person@example.com"]


def test_loader_rejects_unsupported_contact_kind():
    loader = loadUser()
    loader.add_user("instagram", "person")

    with pytest.raises(ValueError, match="Unsupported contact kind"):
        loader.send_steps()
