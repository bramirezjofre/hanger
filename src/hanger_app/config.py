import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    secret_key: str
    admin_token: str
    database_path: Path
    upload_dir: Path
    public_url: str
    production: bool
    max_upload_bytes: int = 5 * 1024 * 1024

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "Settings":
        values = os.environ if environ is None else environ
        production = values.get("HANGER_ENV", "development").lower() == "production"
        secret_key = values.get("HANGER_SECRET_KEY", "")
        admin_token = values.get("HANGER_ADMIN_TOKEN", "")
        if production and not secret_key:
            raise RuntimeError("HANGER_SECRET_KEY is required in production")
        if production and not admin_token:
            raise RuntimeError("HANGER_ADMIN_TOKEN is required in production")

        instance_dir = Path(
            values.get("HANGER_INSTANCE_DIR", PROJECT_ROOT / "instance")
        )
        return cls(
            secret_key=secret_key or "development-only-secret",
            admin_token=admin_token or "development-only-admin-token",
            database_path=Path(
                values.get("HANGER_DB_PATH", instance_dir / "hanger.sqlite3")
            ),
            upload_dir=Path(values.get("HANGER_UPLOAD_DIR", instance_dir / "uploads")),
            public_url=values.get("HANGER_PUBLIC_URL", "http://127.0.0.1:5000"),
            production=production,
        )

    def flask_config(self) -> dict:
        return {
            "SECRET_KEY": self.secret_key,
            "ADMIN_TOKEN": self.admin_token,
            "DATABASE_PATH": str(self.database_path),
            "UPLOAD_DIR": str(self.upload_dir),
            "PUBLIC_URL": self.public_url.rstrip("/"),
            "MAX_CONTENT_LENGTH": self.max_upload_bytes,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
            "SESSION_COOKIE_SECURE": self.production,
        }
