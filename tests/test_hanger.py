import importlib
import sys


PASSWORD = "SecurePass1!"


def load_application(monkeypatch, tmp_path):
    monkeypatch.setenv("HANGER_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("HANGER_SECRET_KEY", "test-secret")
    sys.modules.pop("hanger", None)
    return importlib.import_module("hanger")


def test_registration_login_and_escaped_chat(monkeypatch, tmp_path):
    hanger = load_application(monkeypatch, tmp_path)
    client = hanger.web.test_client()

    registration = client.post(
        "/registered",
        data={
            "userName": "alice",
            "userPassword": PASSWORD,
            "verifyPassword": PASSWORD,
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/hanger-app",
        data={"hanger-user": "alice", "hanger-password": PASSWORD},
    )
    assert login.status_code == 200

    chat = client.post("/chatting", data={"message": "<script>alert(1)</script>"})
    assert chat.status_code == 200
    assert b"<script>" not in chat.data
    assert b"&lt;script&gt;" in chat.data


def test_chat_requires_authentication(monkeypatch, tmp_path):
    hanger = load_application(monkeypatch, tmp_path)
    response = hanger.web.test_client().post("/chatting", data={"message": "Hi"})

    assert response.status_code == 401
