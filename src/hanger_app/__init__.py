import hmac
import secrets
from pathlib import Path
from typing import Optional

import click
from flask import Flask, abort, request, session

from .config import PROJECT_ROOT, Settings
from .db import Database
from .repositories import (
    InvitationRepository,
    JobRepository,
    MessageRepository,
    PostRepository,
    RateLimitRepository,
    UserRepository,
)
from .routes import bp
from .services import AuthService, DeliveryGateway, InvitationService, JobWorker
from .uploads import UploadService


def create_app(test_config: Optional[dict] = None) -> Flask:
    settings = Settings.from_env()
    app = Flask(__name__, template_folder="templates")
    app.config.from_mapping(settings.flask_config())
    if test_config:
        app.config.update(test_config)

    database = Database(Path(app.config["DATABASE_PATH"]), PROJECT_ROOT / "migrations")
    database.migrate()
    users = UserRepository(database)
    rate_limits = RateLimitRepository(database)
    jobs = JobRepository(database)
    invitation_repository = InvitationRepository(database)
    messages = MessageRepository(database)
    posts = PostRepository(database)
    invitations = InvitationService(invitation_repository, jobs)
    worker = JobWorker(jobs, invitation_repository, DeliveryGateway())

    app.extensions["hanger"] = {
        "database": database,
        "users": users,
        "jobs": jobs,
        "auth": AuthService(users, rate_limits, jobs, app.config["PUBLIC_URL"]),
        "invitations": invitations,
        "invitation_repository": invitation_repository,
        "messages": messages,
        "posts": posts,
        "uploads": UploadService(
            Path(app.config["UPLOAD_DIR"]), app.config["MAX_CONTENT_LENGTH"]
        ),
        "worker": worker,
    }

    @app.before_request
    def protect_post_requests():
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None
        expected = session.get("_csrf_token", "")
        supplied = request.form.get("csrf_token", "") or request.headers.get(
            "X-CSRF-Token", ""
        )
        if not expected or not supplied or not hmac.compare_digest(expected, supplied):
            abort(400, "Invalid CSRF token")
        return None

    @app.context_processor
    def csrf_context():
        def csrf_token() -> str:
            if "_csrf_token" not in session:
                session["_csrf_token"] = secrets.token_urlsafe(32)
            return session["_csrf_token"]

        return {"csrf_token": csrf_token}

    @app.cli.command("process-jobs")
    @click.option("--limit", default=100, type=int)
    def process_jobs(limit: int):
        processed = 0
        while processed < limit:
            result = worker.process_once()
            if result is None:
                break
            processed += 1
        click.echo(f"Processed {processed} jobs")

    app.register_blueprint(bp)
    return app
