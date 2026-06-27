import os
import re
import secrets
import smtplib
import time
from email.message import EmailMessage
from typing import Optional
from urllib.parse import urlencode

from .models import Application, User
from .repositories import (
    ApplicationRepository,
    InvitationRepository,
    JobRepository,
    RateLimitRepository,
    UserRepository,
)
from .security import hash_password, hash_token, valid_password, verify_password


class RateLimitExceeded(Exception):
    pass


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        rate_limits: RateLimitRepository,
        jobs: JobRepository,
        invitations: InvitationRepository,
        public_url: str,
        require_invitation: bool = False,
    ):
        self.users = users
        self.rate_limits = rate_limits
        self.jobs = jobs
        self.invitations = invitations
        self.public_url = public_url
        self.require_invitation = require_invitation

    def register(
        self,
        username: str,
        password: str,
        age: Optional[int] = None,
        contact_kind: Optional[str] = None,
        contact_address: Optional[str] = None,
        role: str = "user",
        invitation_token: Optional[str] = None,
    ) -> bool:
        username = username.strip()
        kind = contact_kind.strip().lower() if contact_kind else None
        address = contact_address.strip() if contact_address else None
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,64}", username):
            raise ValueError("Username must be 3-64 safe characters")
        if age is not None and not 1 <= age <= 130:
            raise ValueError("Age must be between 1 and 130")
        if not valid_password(password):
            raise ValueError("Password does not meet the security requirements")
        if bool(kind) != bool(address):
            raise ValueError("Contact kind and address must be provided together")
        if kind in {"email", "mail"} and not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+", address or ""
        ):
            raise ValueError("Invalid email address")
        if kind in {"phone", "sms", "tel"} and not re.fullmatch(
            r"\+?[1-9]\d{7,14}", address or ""
        ):
            raise ValueError("Invalid phone number")
        if role not in {"user", "admin"}:
            raise ValueError("Unsupported role")
        password_hash = hash_password(password)
        if self.require_invitation and role == "user":
            if not kind or not address:
                raise ValueError("Contact kind and address are required for invitation")
            token = invitation_token.strip() if invitation_token else ""
            if not token:
                raise ValueError("A valid invitation token is required")
            created = self.users.create_with_invitation(
                username,
                password_hash,
                age,
                kind,
                address,
                role,
                hash_token(token),
                int(time.time()),
            )
            if created is None:
                raise ValueError("Invalid or expired invitation token")
            return created
        return self.users.create(
            username, password_hash, age, kind, address, role
        )

    def login(self, username: str, password: str, client_key: str) -> Optional[User]:
        normalized = username.strip()
        key = f"login:{client_key}:{normalized.lower()}"
        if not self.rate_limits.allow(key, limit=10, window_seconds=300):
            raise RateLimitExceeded("Too many login attempts")
        found = self.users.get(normalized)
        if found is None or not verify_password(password, found.password_hash):
            return None
        return found

    def request_password_recovery(self, username: str, client_key: str) -> None:
        normalized = username.strip()
        key = f"recovery:{client_key}:{normalized.lower()}"
        if not self.rate_limits.allow(key, limit=5, window_seconds=3600):
            raise RateLimitExceeded("Too many recovery attempts")

        found = self.users.get(normalized)
        if found is None or not found.contact_address or not found.contact_kind:
            return

        token = secrets.token_urlsafe(32)
        query = urlencode({"user": normalized, "token": token})
        reset_url = f"{self.public_url}/password-recovery?{query}"
        bucket = int(time.time()) // 60
        self.users.queue_recovery(
            normalized,
            hash_token(token),
            int(time.time()) + 900,
            {
                "address": found.contact_address,
                "kind": found.contact_kind,
                "reset_url": reset_url,
            },
            f"recovery:{found.id}:{bucket}",
        )

    def recover_password(self, username: str, token: str, new_password: str) -> bool:
        if not valid_password(new_password):
            raise ValueError("Password does not meet the security requirements")
        return self.users.consume_recovery(
            username.strip(),
            hash_token(token),
            int(time.time()),
            hash_password(new_password),
        )


class InvitationService:
    def __init__(self, invitations: InvitationRepository, jobs: JobRepository):
        self.invitations = invitations
        self.jobs = jobs

    def invite(
        self,
        address: str,
        kind: str,
        registration_url: str,
        application_id: Optional[int] = None,
        ttl_seconds: int = 7 * 24 * 60 * 60,
    ) -> bool:
        normalized_address = address.strip()
        normalized_kind = kind.strip().lower()
        if not normalized_address or normalized_kind not in {
            "email",
            "mail",
            "phone",
            "sms",
            "tel",
        }:
            raise ValueError("A supported contact address and kind are required")
        token = secrets.token_urlsafe(32)
        separator = "&" if "?" in registration_url else "?"
        url = f"{registration_url}{separator}{urlencode({'token': token})}"
        return self.invitations.add_with_job(
            normalized_address,
            normalized_kind,
            {
                "address": normalized_address,
                "kind": normalized_kind,
                "registration_url": url,
            },
            f"invitation:{normalized_kind}:{normalized_address.lower()}",
            hash_token(token),
            int(time.time()) + ttl_seconds,
            application_id,
        )


class ApplicationService:
    def __init__(
        self,
        applications: ApplicationRepository,
        invitations: InvitationService,
    ):
        self.applications = applications
        self.invitations = invitations

    @staticmethod
    def _normalize_contact(address: str, kind: str) -> tuple[str, str]:
        normalized_address = address.strip()
        normalized_kind = kind.strip().lower()
        if not normalized_address or normalized_kind not in {
            "email",
            "mail",
            "phone",
            "sms",
            "tel",
        }:
            raise ValueError("A supported contact address and kind are required")
        if normalized_kind in {"email", "mail"} and not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized_address
        ):
            raise ValueError("Invalid email address")
        if normalized_kind in {"phone", "sms", "tel"} and not re.fullmatch(
            r"\+?[1-9]\d{7,14}", normalized_address
        ):
            raise ValueError("Invalid phone number")
        return normalized_address, normalized_kind

    def submit(
        self,
        username: Optional[str],
        contact_address: str,
        contact_kind: str,
        answers: Optional[dict] = None,
    ) -> tuple[Optional[Application], bool]:
        address, kind = self._normalize_contact(contact_address, contact_kind)
        normalized_username = username.strip() if username else None
        return self.applications.create(normalized_username, address, kind, answers)

    def list_all(self, status: Optional[str] = None) -> list[Application]:
        return self.applications.list_all(status)

    def accept(
        self, application_id: int, reviewer_username: str, notes: Optional[str] = None
    ) -> bool:
        return self.applications.transition(
            application_id, "accepted", reviewer_username, notes
        )

    def reject(
        self, application_id: int, reviewer_username: str, notes: Optional[str] = None
    ) -> bool:
        return self.applications.transition(
            application_id, "rejected", reviewer_username, notes
        )

    def invite(
        self, application_id: int, reviewer_username: str, registration_url: str
    ) -> bool:
        application = self.applications.get(application_id)
        if application is None:
            raise LookupError("Application not found")
        if application.status == "invited":
            return False
        if application.status != "accepted":
            raise ValueError("Only accepted applications can be invited")
        created = self.invitations.invite(
            application.contact_address,
            application.contact_kind,
            registration_url,
            application.id,
        )
        if created:
            self.applications.transition(application.id, "invited", reviewer_username)
        return created


class DeliveryGateway:
    def send(self, kind: str, address: str, content: str) -> None:
        if kind in {"email", "mail"}:
            self._email(address, content)
        elif kind in {"phone", "sms", "tel"}:
            self._sms(address, content)
        else:
            raise ValueError(f"Unsupported delivery kind: {kind}")

    @staticmethod
    def _email(address: str, content: str) -> None:
        username = os.environ.get("HANGER_SMTP_USER")
        password = os.environ.get("HANGER_SMTP_PASSWORD")
        if not username or not password:
            raise RuntimeError("SMTP credentials are not configured")
        message = EmailMessage()
        message["Subject"] = "Hanger notification"
        message["From"] = username
        message["To"] = address
        message.set_content(content)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(username, password)
            server.send_message(message)

    @staticmethod
    def _sms(address: str, content: str) -> None:
        sid = os.environ.get("TWILIO_ACCOUNT_SID")
        token = os.environ.get("TWILIO_AUTH_TOKEN")
        phone = os.environ.get("TWILIO_PHONE_NUMBER")
        if not sid or not token or not phone:
            raise RuntimeError("Twilio credentials are not configured")
        try:
            from twilio.http.http_client import TwilioHttpClient
            from twilio.rest import Client
        except ImportError as error:
            raise RuntimeError("Twilio support is not installed") from error
        http_client = TwilioHttpClient(timeout=10)
        Client(sid, token, http_client=http_client).messages.create(
            body=content, from_=phone, to=address
        )


class JobWorker:
    def __init__(
        self,
        jobs: JobRepository,
        invitations: InvitationRepository,
        gateway: DeliveryGateway,
    ):
        self.jobs = jobs
        self.invitations = invitations
        self.gateway = gateway

    def process_once(self) -> Optional[bool]:
        job = self.jobs.claim_next()
        if job is None:
            return None
        try:
            if job.kind == "registration_invitation":
                self.gateway.send(
                    job.payload["kind"],
                    job.payload["address"],
                    f"Register at {job.payload['registration_url']}",
                )
                self.invitations.mark_sent(job.payload["invitation_id"])
            elif job.kind == "password_recovery":
                self.gateway.send(
                    job.payload["kind"],
                    job.payload["address"],
                    f"Reset your password at {job.payload['reset_url']}",
                )
            else:
                raise ValueError(f"Unknown job kind: {job.kind}")
        except Exception as error:
            self.jobs.fail(job, str(error))
            return False
        return self.jobs.complete(job)
