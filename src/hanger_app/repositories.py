import json
import sqlite3
import time
import uuid
from typing import Optional

from .db import Database
from .models import Application, Job, Message, Post, User


class UserRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(
        self,
        username: str,
        password_hash: str,
        age: Optional[int],
        contact_kind: Optional[str],
        contact_address: Optional[str],
        role: str = "user",
    ) -> bool:
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO users
                        (username, password_hash, age, contact_kind,
                         contact_address, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, age, contact_kind, contact_address, role),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def create_with_invitation(
        self,
        username: str,
        password_hash: str,
        age: Optional[int],
        contact_kind: Optional[str],
        contact_address: Optional[str],
        role: str,
        invitation_token_hash: str,
        now: int,
    ) -> Optional[bool]:
        try:
            with self.database.transaction(immediate=True) as connection:
                invitation = connection.execute(
                    """
                    SELECT id, contact_address, contact_kind
                    FROM invitations
                    WHERE token_hash = ?
                        AND used_at IS NULL
                        AND (expires_at IS NULL OR expires_at >= ?)
                    """,
                    (invitation_token_hash, now),
                ).fetchone()
                if invitation is None:
                    return None
                if contact_kind and invitation["contact_kind"] != contact_kind:
                    return None
                if contact_address and invitation["contact_address"] != contact_address:
                    return None

                connection.execute(
                    """
                    INSERT INTO users
                        (username, password_hash, age, contact_kind,
                         contact_address, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        password_hash,
                        age,
                        contact_kind,
                        contact_address,
                        role,
                    ),
                )
                connection.execute(
                    """
                    UPDATE invitations
                    SET status = 'used', used_at = ?
                    WHERE id = ?
                    """,
                    (now, invitation["id"]),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def get(self, username: str) -> Optional[User]:
        with self.database.transaction() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash, age, contact_kind,
                       contact_address, role
                FROM users WHERE username = ?
                """,
                (username,),
            ).fetchone()
        return User(**dict(row)) if row else None

    def queue_recovery(
        self,
        username: str,
        token_hash: str,
        expires: int,
        payload: dict,
        idempotency_key: str,
    ) -> bool:
        try:
            with self.database.transaction(immediate=True) as connection:
                result = connection.execute(
                    """
                    UPDATE users SET recovery_token_hash = ?, recovery_expires = ?
                    WHERE username = ?
                    """,
                    (token_hash, expires, username),
                )
                if result.rowcount != 1:
                    return False
                connection.execute(
                    """
                    INSERT INTO jobs (kind, payload_json, idempotency_key)
                    VALUES ('password_recovery', ?, ?)
                    """,
                    (json.dumps(payload), idempotency_key),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def set_role(self, username: str, role: str) -> bool:
        if role not in {"user", "admin"}:
            raise ValueError("Unsupported role")
        with self.database.transaction() as connection:
            result = connection.execute(
                """
                UPDATE users SET role = ?
                WHERE username = ?
                """,
                (role, username),
            )
        return result.rowcount == 1

    def consume_recovery(
        self, username: str, token_hash: str, now: int, password_hash: str
    ) -> bool:
        with self.database.transaction(immediate=True) as connection:
            result = connection.execute(
                """
                UPDATE users
                SET password_hash = ?, recovery_token_hash = NULL,
                    recovery_expires = NULL
                WHERE username = ? AND recovery_token_hash = ?
                    AND recovery_expires >= ?
                """,
                (password_hash, username, token_hash, now),
            )
        return result.rowcount == 1


class RateLimitRepository:
    def __init__(self, database: Database):
        self.database = database

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = int(time.time())
        with self.database.transaction(immediate=True) as connection:
            connection.execute(
                "DELETE FROM rate_limits WHERE window_started < ?", (now - 86400,)
            )
            row = connection.execute(
                "SELECT window_started, attempts FROM rate_limits WHERE key = ?",
                (key,),
            ).fetchone()
            if row is None or now - row["window_started"] >= window_seconds:
                connection.execute(
                    """
                    INSERT INTO rate_limits (key, window_started, attempts)
                    VALUES (?, ?, 1)
                    ON CONFLICT(key) DO UPDATE SET
                        window_started = excluded.window_started, attempts = 1
                    """,
                    (key, now),
                )
                return True
            if row["attempts"] >= limit:
                return False
            connection.execute(
                "UPDATE rate_limits SET attempts = attempts + 1 WHERE key = ?", (key,)
            )
            return True


class AuditRepository:
    def __init__(self, database: Database):
        self.database = database

    def record(self, actor: str, action: str, target: Optional[str] = None) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO audit_log (actor_id, action, target)
                SELECT id, ?, ? FROM users WHERE username = ?
                """,
                (action, target, actor),
            )


class ApplicationRepository:
    VALID_STATUSES = {
        "submitted",
        "screening",
        "interview",
        "accepted",
        "rejected",
        "invited",
    }

    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _application_from_row(row: sqlite3.Row) -> Application:
        data = dict(row)
        data["answers"] = json.loads(data.pop("answers_json"))
        return Application(**data)

    def create(
        self,
        username: Optional[str],
        contact_address: str,
        contact_kind: str,
        answers: Optional[dict] = None,
    ) -> tuple[Optional[Application], bool]:
        try:
            with self.database.transaction() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO applications
                        (username, contact_address, contact_kind, answers_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        username,
                        contact_address,
                        contact_kind,
                        json.dumps(answers or {}),
                    ),
                )
                row = connection.execute(
                    """
                    SELECT id, username, contact_address, contact_kind,
                           answers_json, reviewer_notes, reviewer_id, status,
                           decided_at, created_at, updated_at
                    FROM applications WHERE id = ?
                    """,
                    (cursor.lastrowid,),
                ).fetchone()
        except sqlite3.IntegrityError:
            return None, False
        return self._application_from_row(row), True

    def get(self, application_id: int) -> Optional[Application]:
        with self.database.transaction() as connection:
            row = connection.execute(
                """
                SELECT id, username, contact_address, contact_kind, answers_json,
                       reviewer_notes, reviewer_id, status, decided_at, created_at,
                       updated_at
                FROM applications WHERE id = ?
                """,
                (application_id,),
            ).fetchone()
        return self._application_from_row(row) if row else None

    def list_all(self, status: Optional[str] = None) -> list[Application]:
        parameters: tuple = ()
        where = ""
        if status:
            if status not in self.VALID_STATUSES:
                raise ValueError("Unsupported application status")
            where = "WHERE status = ?"
            parameters = (status,)
        with self.database.transaction() as connection:
            rows = connection.execute(
                f"""
                SELECT id, username, contact_address, contact_kind, answers_json,
                       reviewer_notes, reviewer_id, status, decided_at, created_at,
                       updated_at
                FROM applications
                {where}
                ORDER BY id DESC
                """,
                parameters,
            ).fetchall()
        return [self._application_from_row(row) for row in rows]

    def transition(
        self,
        application_id: int,
        status: str,
        reviewer_username: str,
        notes: Optional[str] = None,
    ) -> bool:
        if status not in self.VALID_STATUSES:
            raise ValueError("Unsupported application status")
        decided_at = "unixepoch()" if status in {"accepted", "rejected"} else "NULL"
        with self.database.transaction() as connection:
            result = connection.execute(
                f"""
                UPDATE applications
                SET status = ?,
                    reviewer_notes = COALESCE(?, reviewer_notes),
                    reviewer_id = (
                        SELECT id FROM users WHERE username = ?
                    ),
                    decided_at = {decided_at},
                    updated_at = unixepoch()
                WHERE id = ?
                """,
                (status, notes, reviewer_username, application_id),
            )
        return result.rowcount == 1


class InvitationRepository:
    def __init__(self, database: Database):
        self.database = database

    def add(self, address: str, kind: str) -> tuple[int, bool]:
        with self.database.transaction() as connection:
            existing = connection.execute(
                """
                SELECT id FROM invitations
                WHERE contact_address = ? AND contact_kind = ?
                """,
                (address, kind),
            ).fetchone()
            if existing:
                return existing["id"], False
            cursor = connection.execute(
                """
                INSERT INTO invitations (contact_address, contact_kind)
                VALUES (?, ?)
                """,
                (address, kind),
            )
            return cursor.lastrowid, True

    def add_with_job(
        self,
        address: str,
        kind: str,
        payload: dict,
        idempotency_key: str,
        token_hash: Optional[str] = None,
        expires_at: Optional[int] = None,
        application_id: Optional[int] = None,
    ) -> bool:
        try:
            with self.database.transaction(immediate=True) as connection:
                existing = connection.execute(
                    """
                    SELECT id FROM invitations
                    WHERE contact_address = ? AND contact_kind = ?
                    """,
                    (address, kind),
                ).fetchone()
                if existing:
                    return False
                cursor = connection.execute(
                    """
                    INSERT INTO invitations
                        (contact_address, contact_kind, token_hash, expires_at,
                         application_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (address, kind, token_hash, expires_at, application_id),
                )
                payload["invitation_id"] = cursor.lastrowid
                connection.execute(
                    """
                    INSERT INTO jobs (kind, payload_json, idempotency_key)
                    VALUES ('registration_invitation', ?, ?)
                    """,
                    (json.dumps(payload), idempotency_key),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def list_all(self) -> list[dict]:
        with self.database.transaction() as connection:
            rows = connection.execute(
                """
                SELECT id, contact_address, contact_kind, status, created_at, sent_at,
                       application_id, expires_at, used_at
                FROM invitations ORDER BY id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_sent(self, invitation_id: int) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                UPDATE invitations SET status = 'sent', sent_at = unixepoch()
                WHERE id = ?
                """,
                (invitation_id,),
            )

    def link_application_invited(self, application_id: int) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                UPDATE applications
                SET status = 'invited', updated_at = unixepoch()
                WHERE id = ?
                """,
                (application_id,),
            )


class JobRepository:
    def __init__(self, database: Database):
        self.database = database

    def enqueue(self, kind: str, payload: dict, idempotency_key: str) -> bool:
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO jobs (kind, payload_json, idempotency_key)
                    VALUES (?, ?, ?)
                    """,
                    (kind, json.dumps(payload), idempotency_key),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def claim_next(self) -> Optional[Job]:
        now = int(time.time())
        lease_id = uuid.uuid4().hex
        with self.database.transaction(immediate=True) as connection:
            row = connection.execute(
                """
                SELECT id, kind, payload_json, attempts FROM jobs
                WHERE attempts < 5 AND (
                    (status IN ('pending', 'failed') AND available_at <= ?)
                    OR (status = 'running' AND locked_at <= ?)
                )
                ORDER BY id LIMIT 1
                """,
                (now, now - 300),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                """
                UPDATE jobs SET status = 'running', attempts = attempts + 1,
                    lease_id = ?, locked_at = ?
                WHERE id = ?
                """,
                (lease_id, now, row["id"]),
            )
        return Job(
            id=row["id"],
            kind=row["kind"],
            payload=json.loads(row["payload_json"]),
            attempts=row["attempts"] + 1,
            lease_id=lease_id,
        )

    def complete(self, job: Job) -> bool:
        with self.database.transaction() as connection:
            result = connection.execute(
                """
                UPDATE jobs SET status = 'completed', completed_at = unixepoch(),
                    lease_id = NULL, locked_at = NULL
                WHERE id = ? AND lease_id = ?
                """,
                (job.id, job.lease_id),
            )
        return result.rowcount == 1

    def fail(self, job: Job, error: str) -> None:
        retry_at = int(time.time()) + min(300, 2**job.attempts)
        with self.database.transaction() as connection:
            connection.execute(
                """
                UPDATE jobs SET status = 'failed', available_at = ?, last_error = ?,
                    lease_id = NULL, locked_at = NULL
                WHERE id = ? AND lease_id = ?
                """,
                (retry_at, error[:500], job.id, job.lease_id),
            )

    def list_all(self) -> list[dict]:
        with self.database.transaction() as connection:
            rows = connection.execute("SELECT * FROM jobs ORDER BY id").fetchall()
        return [dict(row) for row in rows]


class MessageRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(
        self,
        sender: str,
        receiver: str,
        content: str,
        attachment: Optional[dict] = None,
    ) -> Message:
        with self.database.transaction() as connection:
            people = {
                row["username"]: row["id"]
                for row in connection.execute(
                    "SELECT id, username FROM users WHERE username IN (?, ?)",
                    (sender, receiver),
                )
            }
            if sender not in people or receiver not in people:
                raise LookupError("Sender or receiver does not exist")
            cursor = connection.execute(
                """
                INSERT INTO messages (sender_id, receiver_id, content)
                VALUES (?, ?, ?)
                """,
                (people[sender], people[receiver], content),
            )
            if attachment:
                connection.execute(
                    """
                    INSERT INTO attachments
                        (message_id, stored_name, original_name, mime_type, size)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        cursor.lastrowid,
                        attachment["stored_name"],
                        attachment["original_name"],
                        attachment["mime_type"],
                        attachment["size"],
                    ),
                )
            row = connection.execute(
                """
                SELECT message.id, sender.username AS sender,
                       receiver.username AS receiver, message.content,
                       message.created_at
                FROM messages AS message
                JOIN users AS sender ON sender.id = message.sender_id
                JOIN users AS receiver ON receiver.id = message.receiver_id
                WHERE message.id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
        return Message(**dict(row))

    def can_access_attachment(self, stored_name: str, username: str) -> bool:
        with self.database.transaction() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM attachments AS attachment
                JOIN messages AS message ON message.id = attachment.message_id
                JOIN users AS sender ON sender.id = message.sender_id
                JOIN users AS receiver ON receiver.id = message.receiver_id
                WHERE attachment.stored_name = ?
                    AND ? IN (sender.username, receiver.username)
                """,
                (stored_name, username),
            ).fetchone()
        return row is not None


class PostRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(self, author: str, content: str) -> Post:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """
                INSERT INTO posts (author_id, content)
                SELECT id, ? FROM users WHERE username = ?
                """,
                (content, author),
            )
            if cursor.rowcount != 1:
                raise LookupError("Author does not exist")
            row = connection.execute(
                """
                SELECT post.id, user.username AS author, post.content,
                       post.created_at
                FROM posts AS post
                JOIN users AS user ON user.id = post.author_id
                WHERE post.id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
        return Post(**dict(row))

    def list_all(self) -> list[Post]:
        with self.database.transaction() as connection:
            rows = connection.execute(
                """
                SELECT post.id, user.username AS author, post.content,
                       post.created_at
                FROM posts AS post
                JOIN users AS user ON user.id = post.author_id
                ORDER BY post.id DESC
                """
            ).fetchall()
        return [Post(**dict(row)) for row in rows]

    def comment(self, post_id: int, author: str, content: str) -> bool:
        with self.database.transaction() as connection:
            result = connection.execute(
                """
                INSERT INTO comments (post_id, author_id, content)
                SELECT post.id, user.id, ?
                FROM posts AS post, users AS user
                WHERE post.id = ? AND user.username = ?
                """,
                (content, post_id, author),
            )
        return result.rowcount == 1

    def like(self, post_id: int, username: str) -> Optional[bool]:
        try:
            with self.database.transaction() as connection:
                result = connection.execute(
                    """
                    INSERT INTO post_likes (post_id, user_id)
                    SELECT post.id, user.id
                    FROM posts AS post, users AS user
                    WHERE post.id = ? AND user.username = ?
                    """,
                    (post_id, username),
                )
                if result.rowcount != 1:
                    return None
        except sqlite3.IntegrityError:
            return False
        return True
