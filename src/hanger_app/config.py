import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_path: Path
    upload_dir: Path
    public_url: str
    production: bool
    auto_migrate: bool
    trust_proxy: bool
    require_invitation: bool
    max_upload_bytes: int = 5 * 1024 * 1024

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "Settings":
        values = os.environ if environ is None else environ
        production = values.get("HANGER_ENV", "development").lower() == "production"
        secret_key = values.get("HANGER_SECRET_KEY", "")
        if production and not secret_key:
            raise RuntimeError("HANGER_SECRET_KEY is required in production")
        required_storage = ("HANGER_DB_PATH", "HANGER_UPLOAD_DIR", "HANGER_PUBLIC_URL")
        missing = [
            name for name in required_storage if production and not values.get(name)
        ]
        if missing:
            raise RuntimeError(f"Required production settings: {', '.join(missing)}")

        instance_dir = Path(
            values.get("HANGER_INSTANCE_DIR", PROJECT_ROOT / "instance")
        )
        return cls(
            secret_key=secret_key or "development-only-secret",
            database_path=Path(
                values.get("HANGER_DB_PATH", instance_dir / "hanger.sqlite3")
            ),
            upload_dir=Path(values.get("HANGER_UPLOAD_DIR", instance_dir / "uploads")),
            public_url=values.get("HANGER_PUBLIC_URL", "http://127.0.0.1:5000"),
            production=production,
            auto_migrate=values.get(
                "HANGER_AUTO_MIGRATE", "false" if production else "true"
            ).lower()
            == "true",
            trust_proxy=values.get("HANGER_TRUST_PROXY", "false").lower() == "true",
            require_invitation=values.get(
                "HANGER_REQUIRE_INVITATION", "true" if production else "false"
            ).lower()
            == "true",
        )

    def flask_config(self) -> dict:
        return {
            "SECRET_KEY": self.secret_key,
            "DATABASE_PATH": str(self.database_path),
            "UPLOAD_DIR": str(self.upload_dir),
            "PUBLIC_URL": self.public_url.rstrip("/"),
            "MAX_CONTENT_LENGTH": self.max_upload_bytes,
            "AUTO_MIGRATE": self.auto_migrate,
            "TRUST_PROXY": self.trust_proxy,
            "REQUIRE_INVITATION": self.require_invitation,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
            "SESSION_COOKIE_SECURE": self.production,
        }
