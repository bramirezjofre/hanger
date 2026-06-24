import hashlib
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: Path, migrations_dir: Path):
        self.path = Path(path)
        self.migrations_dir = Path(migrations_dir)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path), timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def transaction(self, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            if immediate:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> None:
        connection = self.connect()
        try:
            connection.execute("BEGIN EXCLUSIVE")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    checksum TEXT,
                    applied_at INTEGER NOT NULL DEFAULT (unixepoch())
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(schema_migrations)")
            }
            if "checksum" not in columns:
                connection.execute(
                    "ALTER TABLE schema_migrations ADD COLUMN checksum TEXT"
                )
            applied = {
                row["version"]: row["checksum"]
                for row in connection.execute(
                    "SELECT version, checksum FROM schema_migrations"
                )
            }
            for migration in sorted(self.migrations_dir.glob("*.sql")):
                script = migration.read_text(encoding="utf-8")
                checksum = hashlib.sha256(script.encode("utf-8")).hexdigest()
                recorded = applied.get(migration.name)
                if migration.name in applied:
                    if recorded is not None and recorded != checksum:
                        raise RuntimeError(f"Migration changed: {migration.name}")
                    if recorded is None:
                        connection.execute(
                            """
                            UPDATE schema_migrations SET checksum = ?
                            WHERE version = ?
                            """,
                            (checksum, migration.name),
                        )
                    continue
                if migration.name != "001_initial.sql":
                    self._migrate_legacy_users(connection)
                for statement in script.split(";"):
                    if statement.strip():
                        connection.execute(statement)
                connection.execute(
                    """
                    INSERT INTO schema_migrations (version, checksum) VALUES (?, ?)
                    ON CONFLICT(version) DO UPDATE SET checksum = excluded.checksum
                    """,
                    (migration.name, checksum),
                )
            self._migrate_legacy_users(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _migrate_legacy_users(connection: sqlite3.Connection) -> None:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if "users" in tables and "hanger_register" in tables:
            connection.execute(
                """
                INSERT OR IGNORE INTO users (username, password_hash)
                SELECT user, password FROM hanger_register
                WHERE user IS NOT NULL AND password IS NOT NULL
                """
            )
