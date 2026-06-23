import hashlib
import hmac
import os
import secrets
import smtplib
import sqlite3
import time
from email.message import EmailMessage
from pathlib import Path
from typing import List, Optional, Union

from . import user


web: user.HangerApp = user.HangerApp()


class loadUser:
    """Collect approved contacts and send their registration link."""

    def __init__(self):
        self.contacts: dict[str, str] = {}

    def add_user(self, kind: str, contact_address: str) -> bool:
        address = contact_address.strip()
        contact_kind = kind.strip().lower()
        if not address or not contact_kind:
            raise ValueError("Contact address and kind are required")
        if address in self.contacts:
            return False
        self.contacts[address] = contact_kind
        return True

    def send_steps(self) -> List[str]:
        sent_to: List[str] = []
        for address, kind in self.contacts.items():
            if kind in {"mail", "email"}:
                self._send_email(address)
            elif kind in {"tel", "phone", "sms"}:
                self._send_sms(address)
            else:
                raise ValueError(f"Unsupported contact kind: {kind}")
            sent_to.append(address)
        return sent_to

    def _send_email(self, address: str) -> None:
        username = os.environ.get("HANGER_SMTP_USER")
        password = os.environ.get("HANGER_SMTP_PASSWORD")
        if not username or not password:
            raise RuntimeError("SMTP credentials are not configured")

        message = EmailMessage()
        message["Subject"] = "Hanger registration steps"
        message["From"] = username
        message["To"] = address
        message.set_content(f"Register at {web.domain}/hangerSteps.html")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(username, password)
            server.send_message(message)

    def _send_sms(self, address: str) -> None:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        phone = os.environ.get("TWILIO_PHONE_NUMBER")
        if not account_sid or not auth_token or not phone:
            raise RuntimeError("Twilio credentials are not configured")

        try:
            from twilio.rest import Client
        except ImportError as error:
            raise RuntimeError("Twilio support is not installed") from error

        Client(account_sid, auth_token).messages.create(
            body=f"Register at {web.domain}/hangerSteps.html",
            from_=phone,
            to=address,
        )


class HangerSteps:
    """Registration, authentication, and password recovery service."""

    HASH_ITERATIONS = 600_000

    def __init__(self, database: Union[str, Path] = "registered_users.db"):
        self.new_user: user.Profile = user.Profile()
        self.app: user.HangerApp = user.HangerApp()
        self.database = Path(database)
        with self._connect() as connection:
            self._ensure_schema(connection)

    @staticmethod
    def valid(text: str) -> bool:
        return (
            len(text) >= 12
            and any(character.islower() for character in text)
            and any(character.isupper() for character in text)
            and any(character.isdigit() for character in text)
            and any(not character.isalnum() for character in text)
        )

    def register(self, user_name: str, password: str) -> bool:
        username = user_name.strip()
        if not username:
            raise ValueError("Username is required")
        if not self.valid(password):
            raise ValueError("Password does not meet the security requirements")

        try:
            with self._connect() as connection:
                self._ensure_schema(connection)
                connection.execute(
                    "INSERT INTO hanger_register (user, password) VALUES (?, ?)",
                    (username, self._hash_password(password)),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def login(self, username: str, password: str) -> bool:
        with self._connect() as connection:
            self._ensure_schema(connection)
            row = connection.execute(
                "SELECT password FROM hanger_register WHERE user = ?",
                (username.strip(),),
            ).fetchone()

        if row is None or not self._verify_password(password, row[0]):
            return False

        self.new_user.name = username.strip()
        self.app.logged_user = self.new_user
        return True

    def create_password_recovery_token(
        self, username: str, ttl_seconds: int = 900
    ) -> Optional[str]:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        expires_at = int(time.time()) + ttl_seconds

        with self._connect() as connection:
            self._ensure_schema(connection)
            result = connection.execute(
                """
                UPDATE hanger_register
                SET recovery_token_hash = ?, recovery_expires = ?
                WHERE user = ?
                """,
                (token_hash, expires_at, username.strip()),
            )
        return token if result.rowcount == 1 else None

    def password_recovery(
        self, username: str, token: str, new_password: str
    ) -> bool:
        if not self.valid(new_password):
            raise ValueError("Password does not meet the security requirements")

        with self._connect() as connection:
            self._ensure_schema(connection)
            row = connection.execute(
                """
                SELECT recovery_token_hash, recovery_expires
                FROM hanger_register
                WHERE user = ?
                """,
                (username.strip(),),
            ).fetchone()
            if row is None or row[0] is None or row[1] is None:
                return False

            supplied_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            if int(row[1]) < int(time.time()) or not hmac.compare_digest(
                supplied_hash, row[0]
            ):
                return False

            connection.execute(
                """
                UPDATE hanger_register
                SET password = ?, recovery_token_hash = NULL,
                    recovery_expires = NULL
                WHERE user = ?
                """,
                (self._hash_password(new_password), username.strip()),
            )
        return True

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.database))

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hanger_register (
                user TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                recovery_token_hash TEXT,
                recovery_expires INTEGER
            )
            """
        )
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(hanger_register)")
        }
        if "recovery_token_hash" not in columns:
            connection.execute(
                "ALTER TABLE hanger_register ADD COLUMN recovery_token_hash TEXT"
            )
        if "recovery_expires" not in columns:
            connection.execute(
                "ALTER TABLE hanger_register ADD COLUMN recovery_expires INTEGER"
            )

    @classmethod
    def _hash_password(cls, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, cls.HASH_ITERATIONS
        )
        return f"pbkdf2_sha256${cls.HASH_ITERATIONS}${salt.hex()}${digest.hex()}"

    @staticmethod
    def _verify_password(password: str, encoded: str) -> bool:
        try:
            algorithm, iterations, salt, expected = encoded.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt),
                int(iterations),
            )
        except (TypeError, ValueError):
            return False
        return hmac.compare_digest(digest.hex(), expected)
