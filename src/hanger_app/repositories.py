import json
import sqlite3
import time
from typing import Optional

from .db import Database
from .models import Job, Message, Post, User


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
    ) -> bool:
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO users
                        (username, password_hash, age, contact_kind, contact_address)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, age, contact_kind, contact_address),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def get(self, username: str) -> Optional[User]:
        with self.database.transaction() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash, age, contact_kind, contact_address
                FROM users WHERE username = ?
                """,
                (username,),
            ).fetchone()
        return User(**dict(row)) if row else None

    def set_recovery(self, username: str, token_hash: str, expires: int) -> bool:
        with self.database.transaction() as connection:
            result = connection.execute(
                """
                UPDATE users SET recovery_token_hash = ?, recovery_expires = ?
                WHERE username = ?
                """,
                (token_hash, expires, username),
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

    def list_all(self) -> list[dict]:
        with self.database.transaction() as connection:
            rows = connection.execute(
                """
                SELECT id, contact_address, contact_kind, status, created_at, sent_at
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
        with self.database.transaction(immediate=True) as connection:
            row = connection.execute(
                """
                SELECT id, kind, payload_json, attempts FROM jobs
                WHERE status IN ('pending', 'failed') AND available_at <= ?
                    AND attempts < 5
                ORDER BY id LIMIT 1
                """,
                (now,),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                """
                UPDATE jobs SET status = 'running', attempts = attempts + 1
                WHERE id = ?
                """,
                (row["id"],),
            )
        return Job(
            id=row["id"],
            kind=row["kind"],
            payload=json.loads(row["payload_json"]),
            attempts=row["attempts"] + 1,
        )

    def complete(self, job_id: int) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                UPDATE jobs SET status = 'completed', completed_at = unixepoch()
                WHERE id = ?
                """,
                (job_id,),
            )

    def fail(self, job: Job, error: str) -> None:
        retry_at = int(time.time()) + min(300, 2**job.attempts)
        with self.database.transaction() as connection:
            connection.execute(
                """
                UPDATE jobs SET status = 'failed', available_at = ?, last_error = ?
                WHERE id = ?
                """,
                (retry_at, error[:500], job.id),
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
            cursor = connection.execute(
                "INSERT INTO messages (sender, receiver, content) VALUES (?, ?, ?)",
                (sender, receiver, content),
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
                "SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return Message(**dict(row))


class PostRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(self, author: str, content: str) -> Post:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO posts (author, content) VALUES (?, ?)", (author, content)
            )
            row = connection.execute(
                "SELECT * FROM posts WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return Post(**dict(row))

    def list_all(self) -> list[Post]:
        with self.database.transaction() as connection:
            rows = connection.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
        return [Post(**dict(row)) for row in rows]

    def comment(self, post_id: int, author: str, content: str) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO comments (post_id, author, content) VALUES (?, ?, ?)",
                (post_id, author, content),
            )

    def like(self, post_id: int, username: str) -> bool:
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    "INSERT INTO post_likes (post_id, username) VALUES (?, ?)",
                    (post_id, username),
                )
        except sqlite3.IntegrityError:
            return False
        return True
