import io

from PIL import Image

PASSWORD = "SecurePass1!"


def register_and_login(client, csrf):
    registration = client.post(
        "/register",
        data={
            "csrf_token": csrf,
            "username": "alice",
            "age": "30",
            "contact_kind": "email",
            "contact_address": "alice@example.com",
            "password": PASSWORD,
            "password_confirmation": PASSWORD,
        },
    )
    assert registration.status_code == 302
    login = client.post(
        "/login",
        data={"csrf_token": csrf, "username": "alice", "password": PASSWORD},
        follow_redirects=True,
    )
    assert login.status_code == 200
    with client.session_transaction() as current_session:
        return current_session["_csrf_token"]


def image_bytes():
    content = io.BytesIO()
    Image.new("RGB", (2, 2), color="red").save(content, format="PNG")
    content.seek(0)
    return content


def test_csrf_is_required(client):
    response = client.post("/login", data={"username": "alice", "password": "x"})
    assert response.status_code == 400


def test_chat_persists_message_and_valid_image(app, client, csrf):
    csrf = register_and_login(client, csrf)
    response = client.post(
        "/chatting",
        data={
            "csrf_token": csrf,
            "receiver": "bob",
            "message": "<script>alert(1)</script>",
            "chat_image": (image_bytes(), "../avatar.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"<script>" not in response.data
    assert b"&lt;script&gt;" in response.data
    uploads = list(app.extensions["hanger"]["uploads"].directory.iterdir())
    assert len(uploads) == 1
    assert uploads[0].suffix == ".png"


def test_invalid_upload_is_rejected(client, csrf):
    csrf = register_and_login(client, csrf)
    response = client.post(
        "/chatting",
        data={
            "csrf_token": csrf,
            "receiver": "bob",
            "message": "hello",
            "chat_image": (io.BytesIO(b"not-an-image"), "payload.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_admin_invitation_requires_token(client, csrf):
    denied = client.post(
        "/interviewer",
        data={
            "csrf_token": csrf,
            "contact_kind": "email",
            "contact_address": "alice@example.com",
        },
    )
    assert denied.status_code == 403

    accepted = client.post(
        "/interviewer",
        headers={"X-Admin-Token": "test-admin"},
        data={
            "csrf_token": csrf,
            "contact_kind": "email",
            "contact_address": "alice@example.com",
        },
    )
    assert accepted.status_code == 200
