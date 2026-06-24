import io
import json
from urllib.parse import parse_qs, urlparse

from PIL import Image

PASSWORD = "SecurePass1!"


def create_user(app, username, role="user"):
    assert app.extensions["hanger"]["auth"].register(
        username,
        PASSWORD,
        30,
        "email",
        f"{username}@example.com",
        role,
    )


def login(client, csrf, username):
    response = client.post(
        "/login",
        data={"csrf_token": csrf, "username": username, "password": PASSWORD},
        follow_redirects=True,
    )
    assert response.status_code == 200
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


def test_registration_login_and_health(app, client, csrf):
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
    assert login(client, csrf, "alice")
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200


def test_chat_requires_existing_receiver_and_protects_attachment(app, client, csrf):
    create_user(app, "alice")
    create_user(app, "bob")
    create_user(app, "charlie")
    csrf = login(client, csrf, "alice")

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
    stored_name = next(app.extensions["hanger"]["uploads"].directory.iterdir()).name

    with client.session_transaction() as current_session:
        current_session["username"] = "charlie"
    assert client.get(f"/uploads/{stored_name}").status_code == 404

    with client.session_transaction() as current_session:
        current_session["username"] = "bob"
    assert client.get(f"/uploads/{stored_name}").status_code == 200


def test_unknown_receiver_does_not_leave_upload(app, client, csrf):
    create_user(app, "alice")
    csrf = login(client, csrf, "alice")
    response = client.post(
        "/chatting",
        data={
            "csrf_token": csrf,
            "receiver": "missing",
            "message": "hello",
            "chat_image": (image_bytes(), "avatar.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 404
    assert not list(app.extensions["hanger"]["uploads"].directory.iterdir())


def test_invalid_upload_is_rejected(app, client, csrf):
    create_user(app, "alice")
    create_user(app, "bob")
    csrf = login(client, csrf, "alice")
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


def test_admin_role_is_required_and_audited(app, client, csrf):
    create_user(app, "alice")
    create_user(app, "admin", role="admin")
    csrf = login(client, csrf, "alice")
    denied = client.post(
        "/interviewer",
        data={
            "csrf_token": csrf,
            "contact_kind": "email",
            "contact_address": "guest@example.com",
        },
    )
    assert denied.status_code == 403

    csrf = login(client, csrf, "admin")
    accepted = client.post(
        "/interviewer",
        data={
            "csrf_token": csrf,
            "contact_kind": "email",
            "contact_address": "guest@example.com",
        },
    )
    assert accepted.status_code == 200
    with app.extensions["hanger"]["database"].transaction() as connection:
        audit = connection.execute("SELECT action FROM audit_log").fetchone()
    assert audit["action"] == "invitation.create"


def test_missing_posts_return_404_and_duplicate_like_returns_409(app, client, csrf):
    create_user(app, "alice")
    csrf = login(client, csrf, "alice")
    assert (
        client.post(
            "/posts/999/comments", data={"csrf_token": csrf, "content": "hello"}
        ).status_code
        == 404
    )
    assert client.post("/posts/999/likes", data={"csrf_token": csrf}).status_code == 404

    post = app.extensions["hanger"]["posts"].create("alice", "hello")
    assert (
        client.post(f"/posts/{post.id}/likes", data={"csrf_token": csrf}).status_code
        == 302
    )
    assert (
        client.post(f"/posts/{post.id}/likes", data={"csrf_token": csrf}).status_code
        == 409
    )


def test_password_recovery_is_private_and_single_use(app, client, csrf):
    create_user(app, "alice")
    requested = client.post(
        "/password-recovery/request",
        data={"csrf_token": csrf, "username": "alice"},
    )
    assert requested.status_code == 202
    assert requested.headers["Cache-Control"] == "no-store"
    assert requested.headers["Referrer-Policy"] == "no-referrer"

    job = app.extensions["hanger"]["jobs"].list_all()[0]
    payload = json.loads(job["payload_json"])
    token = parse_qs(urlparse(payload["reset_url"]).query)["token"][0]
    changed = client.post(
        "/password-recovery",
        data={
            "csrf_token": csrf,
            "username": "alice",
            "recovery_token": token,
            "password": "NewSecurePass2@",
            "password_confirmation": "NewSecurePass2@",
        },
    )
    assert changed.status_code == 302
