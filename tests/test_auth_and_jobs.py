import json
import time
from urllib.parse import parse_qs, urlparse

import pytest

from hanger_app.services import JobWorker, RateLimitExceeded

PASSWORD = "SecurePass1!"
NEW_PASSWORD = "NewSecurePass2@"


def test_registration_persists_profile_and_login(app):
    services = app.extensions["hanger"]
    assert services["auth"].register(
        "alice", PASSWORD, 30, "email", "alice@example.com"
    )

    user = services["auth"].login("alice", PASSWORD, "client-a")
    assert user is not None
    assert user.age == 30
    assert user.contact_address == "alice@example.com"
    assert user.role == "user"


def test_login_is_rate_limited(app):
    auth = app.extensions["hanger"]["auth"]
    for _ in range(10):
        assert auth.login("missing", "wrong", "attacker") is None
    with pytest.raises(RateLimitExceeded):
        auth.login("missing", "wrong", "attacker")


def test_recovery_is_delivered_by_single_use_job(app):
    services = app.extensions["hanger"]
    auth = services["auth"]
    auth.register("alice", PASSWORD, None, "email", "alice@example.com")
    auth.request_password_recovery("alice", "client-a")

    job = services["jobs"].list_all()[0]
    payload = json.loads(job["payload_json"])
    token = parse_qs(urlparse(payload["reset_url"]).query)["token"][0]

    assert auth.recover_password("alice", token, NEW_PASSWORD)
    assert not auth.recover_password("alice", token, PASSWORD)
    assert auth.login("alice", NEW_PASSWORD, "client-b") is not None


def test_duplicate_recovery_request_keeps_delivered_token(app):
    services = app.extensions["hanger"]
    auth = services["auth"]
    auth.register("alice", PASSWORD, None, "email", "alice@example.com")
    auth.request_password_recovery("alice", "client-a")
    first_job = services["jobs"].list_all()[0]
    first_payload = json.loads(first_job["payload_json"])
    first_token = parse_qs(urlparse(first_payload["reset_url"]).query)["token"][0]

    auth.request_password_recovery("alice", "client-a")

    assert len(services["jobs"].list_all()) == 1
    assert auth.recover_password("alice", first_token, NEW_PASSWORD)


class SuccessfulGateway:
    def __init__(self):
        self.calls = []

    def send(self, kind, address, content):
        self.calls.append((kind, address, content))


class FailingGateway:
    def send(self, kind, address, content):
        raise RuntimeError("provider unavailable")


def test_invitations_are_idempotent_and_jobs_retry(app):
    services = app.extensions["hanger"]
    invitations = services["invitations"]
    assert invitations.invite("alice@example.com", "email", "http://test/register")
    assert not invitations.invite("alice@example.com", "email", "http://test/register")
    assert len(services["jobs"].list_all()) == 1

    worker = JobWorker(
        services["jobs"],
        services["invitation_repository"],
        FailingGateway(),
    )
    assert not worker.process_once()
    failed = services["jobs"].list_all()[0]
    assert failed["status"] == "failed"
    assert failed["attempts"] == 1
    assert failed["available_at"] > int(time.time())


def test_worker_completes_invitation(app):
    services = app.extensions["hanger"]
    services["invitations"].invite("bob@example.com", "email", "http://test/register")
    gateway = SuccessfulGateway()
    worker = JobWorker(services["jobs"], services["invitation_repository"], gateway)

    assert worker.process_once()
    assert gateway.calls[0][1] == "bob@example.com"
    assert services["jobs"].list_all()[0]["status"] == "completed"
    invitation = services["invitation_repository"].list_all()[0]
    assert invitation["status"] == "sent"


def test_abandoned_running_job_is_reclaimed(app):
    services = app.extensions["hanger"]
    services["invitations"].invite("stale@example.com", "email", "http://test/register")
    first_claim = services["jobs"].claim_next()
    assert first_claim is not None
    with services["database"].transaction() as connection:
        connection.execute(
            "UPDATE jobs SET locked_at = ? WHERE id = ?",
            (int(time.time()) - 301, first_claim.id),
        )

    reclaimed = services["jobs"].claim_next()

    assert reclaimed is not None
    assert reclaimed.id == first_claim.id
    assert reclaimed.lease_id != first_claim.lease_id
    assert reclaimed.attempts == 2
    assert not services["jobs"].complete(first_claim)
