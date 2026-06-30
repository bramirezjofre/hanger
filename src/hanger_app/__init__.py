import hmac
import secrets
import time
from pathlib import Path
from typing import Optional

import click
from flask import Flask, abort, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Settings
from .db import Database
from .repositories import (
    ApplicationRepository,
    AuditRepository,
    InstallationSettingsRepository,
    InvitationRepository,
    JobRepository,
    MessageRepository,
    PostRepository,
    RateLimitRepository,
    UserRepository,
)
from .routes import bp
from .services import (
    ApplicationService,
    AuthService,
    DeliveryGateway,
    InstallationSettingsService,
    InvitationService,
    JobWorker,
)
from .uploads import UploadService


def create_app(test_config: Optional[dict] = None) -> Flask:
    settings = Settings.from_env()
    app = Flask(__name__, template_folder="templates")
    app.config.from_mapping(settings.flask_config())
    if test_config:
        app.config.update(test_config)
    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    migrations_dir = Path(__file__).resolve().parent / "migrations"
    database = Database(Path(app.config["DATABASE_PATH"]), migrations_dir)
    if app.config["AUTO_MIGRATE"]:
        database.migrate()
    users = UserRepository(database)
    rate_limits = RateLimitRepository(database)
    jobs = JobRepository(database)
    application_repository = ApplicationRepository(database)
    installation_settings_repository = InstallationSettingsRepository(database)
    invitation_repository = InvitationRepository(database)
    messages = MessageRepository(database)
    posts = PostRepository(database)
    audit = AuditRepository(database)
    invitations = InvitationService(invitation_repository, jobs)
    applications = ApplicationService(application_repository, invitations, audit)
    installation_settings = InstallationSettingsService(
        installation_settings_repository
    )
    worker = JobWorker(jobs, invitation_repository, DeliveryGateway())
    auth = AuthService(
        users,
        rate_limits,
        jobs,
        invitation_repository,
        app.config["PUBLIC_URL"],
        app.config["REQUIRE_INVITATION"],
    )

    app.extensions["hanger"] = {
        "database": database,
        "users": users,
        "rate_limits": rate_limits,
        "jobs": jobs,
        "auth": auth,
        "audit": audit,
        "applications": applications,
        "application_repository": application_repository,
        "installation_settings": installation_settings,
        "installation_settings_repository": installation_settings_repository,
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

    @app.after_request
    def protect_sensitive_responses(response):
        if request.path.startswith("/password-recovery"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.cli.command("process-jobs")
    @click.option("--limit", default=100, type=int)
    @click.option("--watch", is_flag=True, help="Wait for new jobs continuously")
    def process_jobs(limit: int, watch: bool):
        total = 0
        while watch or total < limit:
            result = worker.process_once()
            if result is None:
                if not watch:
                    break
                time.sleep(2)
                continue
            total += 1
        click.echo(f"Processed {total} jobs")

    @app.cli.command("db-upgrade")
    def db_upgrade():
        database.migrate()
        click.echo("Database migrations applied")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username: str, password: str):
        if not auth.register(username, password, role="admin"):
            raise click.ClickException("Username already exists")
        click.echo(f"Admin created: {username}")

    @app.cli.command("submit-application")
    @click.option("--username", default="")
    @click.option("--contact-address", prompt=True)
    @click.option(
        "--contact-kind",
        prompt=True,
        type=click.Choice(["email", "mail", "phone", "sms", "tel"]),
    )
    def submit_application(
        username: str, contact_address: str, contact_kind: str
    ) -> None:
        application, created = applications.submit(
            username or None, contact_address, contact_kind
        )
        if not created or application is None:
            raise click.ClickException("Application already exists")
        click.echo(f"Application submitted: {application.id}")

    @app.cli.command("review-applications")
    @click.option(
        "--status",
        type=click.Choice(
            ["submitted", "screening", "interview", "accepted", "rejected", "invited"]
        ),
        default=None,
    )
    @click.option(
        "--interview-status",
        type=click.Choice(["not_scheduled", "scheduled", "completed", "cancelled"]),
        default=None,
    )
    def review_applications(
        status: Optional[str], interview_status: Optional[str]
    ) -> None:
        for application in applications.list_all(status, interview_status):
            click.echo(
                "\t".join(
                    [
                        str(application.id),
                        application.status,
                        application.interview_status,
                        application.contact_kind,
                        application.contact_address,
                        application.username or "",
                    ]
                )
            )

    @app.cli.command("accept-application")
    @click.argument("application_id", type=int)
    @click.option("--reviewer", prompt=True)
    @click.option("--notes", default=None)
    def accept_application(
        application_id: int, reviewer: str, notes: Optional[str]
    ) -> None:
        try:
            accepted = applications.accept(application_id, reviewer, notes)
        except PermissionError as error:
            raise click.ClickException(str(error)) from error
        if not accepted:
            raise click.ClickException("Application not found")
        click.echo(f"Application accepted: {application_id}")

    @app.cli.command("reject-application")
    @click.argument("application_id", type=int)
    @click.option("--reviewer", prompt=True)
    @click.option("--notes", default=None)
    def reject_application(
        application_id: int, reviewer: str, notes: Optional[str]
    ) -> None:
        try:
            rejected = applications.reject(application_id, reviewer, notes)
        except PermissionError as error:
            raise click.ClickException(str(error)) from error
        if not rejected:
            raise click.ClickException("Application not found")
        click.echo(f"Application rejected: {application_id}")

    @app.cli.command("invite-application")
    @click.argument("application_id", type=int)
    @click.option("--reviewer", prompt=True)
    def invite_application(application_id: int, reviewer: str) -> None:
        try:
            created = applications.invite(
                application_id,
                reviewer,
                f"{app.config['PUBLIC_URL']}/register",
            )
        except (LookupError, PermissionError, ValueError) as error:
            raise click.ClickException(str(error)) from error
        if not created:
            raise click.ClickException("Invitation already exists")
        click.echo(f"Invitation queued for application: {application_id}")

    @app.cli.command("schedule-interview")
    @click.argument("application_id", type=int)
    @click.option("--reviewer", prompt=True)
    @click.option("--interviewer", prompt=True)
    @click.option(
        "--contact-method",
        prompt=True,
        type=click.Choice(["email", "mail", "phone", "sms", "tel", "video"]),
    )
    @click.option("--preferred-times", prompt=True)
    def schedule_interview(
        application_id: int,
        reviewer: str,
        interviewer: str,
        contact_method: str,
        preferred_times: str,
    ) -> None:
        try:
            updated = applications.schedule_interview(
                application_id,
                reviewer,
                contact_method,
                preferred_times,
                interviewer,
            )
        except ValueError as error:
            raise click.ClickException(str(error)) from error
        if not updated:
            raise click.ClickException(
                "Application, reviewer, or interviewer not found"
            )
        click.echo(f"Interview scheduled for application: {application_id}")

    @app.cli.command("complete-interview")
    @click.argument("application_id", type=int)
    @click.option("--actor", prompt=True)
    def complete_interview(application_id: int, actor: str) -> None:
        if not applications.complete_interview(application_id, actor):
            raise click.ClickException("Application not found or access denied")
        click.echo(f"Interview completed for application: {application_id}")

    @app.cli.command("add-interview-note")
    @click.argument("application_id", type=int)
    @click.option("--author", prompt=True)
    @click.option(
        "--category",
        prompt=True,
        type=click.Choice(["motivation", "fit", "risks", "follow_up"]),
    )
    @click.option("--content", prompt=True)
    def add_interview_note(
        application_id: int,
        author: str,
        category: str,
        content: str,
    ) -> None:
        try:
            note = applications.add_interview_note(
                application_id, author, category, content
            )
        except (PermissionError, ValueError) as error:
            raise click.ClickException(str(error)) from error
        click.echo(f"Interview note added: {note.id}")

    @app.cli.command("list-interview-notes")
    @click.argument("application_id", type=int)
    @click.option("--requester", prompt=True)
    def list_interview_notes(application_id: int, requester: str) -> None:
        try:
            notes = applications.list_interview_notes(application_id, requester)
        except PermissionError as error:
            raise click.ClickException(str(error)) from error
        for note in notes:
            click.echo(
                "\t".join(
                    [
                        str(note.id),
                        note.category,
                        note.author_username or "",
                        note.content,
                    ]
                )
            )

    @app.cli.command("research-export")
    def research_export() -> None:
        click.echo(json_dumps(applications.research_metrics()))

    @app.cli.command("set-role")
    @click.argument("username")
    @click.argument("role", type=click.Choice(["user", "admin"]))
    def set_role(username: str, role: str):
        if not users.set_role(username, role):
            raise click.ClickException("User not found")
        click.echo(f"Updated {username} to {role}")

    @app.cli.command("settings-list")
    @click.option("--public-only", is_flag=True)
    def settings_list(public_only: bool) -> None:
        for setting in installation_settings.list_all(public_only):
            click.echo(
                "\t".join(
                    [
                        setting.key,
                        json_dumps(setting.value),
                        "public" if setting.is_public else "private",
                    ]
                )
            )

    @app.cli.command("settings-get")
    @click.argument("key")
    def settings_get(key: str) -> None:
        try:
            setting = installation_settings.get(key)
        except ValueError as error:
            raise click.ClickException(str(error)) from error
        if setting is None:
            raise click.ClickException("Installation setting not found")
        click.echo(json_dumps(setting.value))

    @app.cli.command("settings-set")
    @click.argument("key")
    @click.argument("value")
    def settings_set(key: str, value: str) -> None:
        try:
            parsed_value = parse_setting_value(value)
            setting = installation_settings.set(key, parsed_value)
        except ValueError as error:
            raise click.ClickException(str(error)) from error
        click.echo(f"Updated {setting.key}: {json_dumps(setting.value)}")

    @app.get("/health/live")
    def health_live():
        return {"status": "ok"}

    @app.get("/health/ready")
    def health_ready():
        try:
            with database.transaction() as connection:
                connection.execute("SELECT 1 FROM schema_migrations").fetchone()
        except Exception:
            return {"status": "not-ready"}, 503
        return {"status": "ready"}

    app.register_blueprint(bp)
    return app


def parse_setting_value(value: str):
    import json

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def json_dumps(value: object) -> str:
    import json

    return json.dumps(value, sort_keys=True)
