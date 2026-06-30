from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from .services import RateLimitExceeded

bp = Blueprint("hanger", __name__)


def _services() -> dict:
    return current_app.extensions["hanger"]


def _client_key() -> str:
    return request.remote_addr or "unknown"


def _require_login() -> str:
    username = session.get("username")
    if not username:
        abort(401)
    return username


def _require_admin() -> str:
    username = _require_login()
    user = _services()["users"].get(username)
    if user is None or user.role != "admin":
        abort(403)
    return username


def _limit(action: str, limit: int, window_seconds: int) -> None:
    identity = session.get("username") or _client_key()
    if not _services()["rate_limits"].allow(
        f"route:{action}:{identity}", limit, window_seconds
    ):
        abort(429)


def _application_json(application) -> dict:
    return {
        "id": application.id,
        "username": application.username,
        "contact_address": application.contact_address,
        "contact_kind": application.contact_kind,
        "status": application.status,
        "interview_contact_method": application.interview_contact_method,
        "interview_preferred_times": application.interview_preferred_times,
        "interviewer_username": application.interviewer_username,
        "interview_status": application.interview_status,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
    }


@bp.get("/")
def index():
    posts = _services()["posts"].list_all()
    return render_template("index.html", posts=posts)


@bp.post("/login")
def login():
    try:
        found = _services()["auth"].login(
            request.form.get("username", ""),
            request.form.get("password", ""),
            _client_key(),
        )
    except RateLimitExceeded as error:
        return render_template("error.html", message=str(error)), 429
    if found is None:
        return render_template(
            "error.html", message="Invalid username or password"
        ), 401
    session.clear()
    session["username"] = found.username
    return redirect(url_for("hanger.index"))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("hanger.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template(
            "register.html", invitation_token=request.args.get("token", "")
        )
    _limit("register", 5, 3600)
    password = request.form.get("password", "")
    if password != request.form.get("password_confirmation", ""):
        return render_template("error.html", message="Passwords do not match"), 400
    age_text = request.form.get("age", "").strip()
    try:
        age = int(age_text) if age_text else None
        created = _services()["auth"].register(
            request.form.get("username", ""),
            password,
            age,
            request.form.get("contact_kind", ""),
            request.form.get("contact_address", ""),
            invitation_token=request.form.get("invitation_token", ""),
        )
    except ValueError as error:
        return render_template("error.html", message=str(error)), 400
    if not created:
        return render_template("error.html", message="Username already exists"), 409
    return redirect(url_for("hanger.index"))


@bp.route("/password-recovery", methods=["GET", "POST"])
def password_recovery():
    if request.method == "GET":
        return render_template(
            "recovery.html",
            username=request.args.get("user", ""),
            recovery_token=request.args.get("token", ""),
        )
    password = request.form.get("password", "")
    if password != request.form.get("password_confirmation", ""):
        return render_template("error.html", message="Passwords do not match"), 400
    try:
        recovered = _services()["auth"].recover_password(
            request.form.get("username", ""),
            request.form.get("recovery_token", ""),
            password,
        )
    except ValueError as error:
        return render_template("error.html", message=str(error)), 400
    if not recovered:
        return render_template("error.html", message="Invalid or expired token"), 400
    return redirect(url_for("hanger.index"))


@bp.post("/password-recovery/request")
def request_password_recovery():
    try:
        _services()["auth"].request_password_recovery(
            request.form.get("username", ""), _client_key()
        )
    except RateLimitExceeded as error:
        return render_template("error.html", message=str(error)), 429
    return render_template(
        "message.html",
        message="If the account exists, recovery instructions were queued.",
    ), 202


@bp.route("/interviewer", methods=["GET", "POST"])
def interviewer():
    admin = _require_admin()
    if request.method == "POST":
        try:
            created = _services()["invitations"].invite(
                request.form.get("contact_address", ""),
                request.form.get("contact_kind", ""),
                f"{current_app.config['PUBLIC_URL']}/register",
            )
            if created:
                _services()["audit"].record(
                    admin, "invitation.create", request.form.get("contact_address", "")
                )
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
    return jsonify({"invitations": _services()["invitation_repository"].list_all()})


@bp.get("/admin/applications")
def admin_applications():
    _require_admin()
    try:
        applications = _services()["applications"].list_all(
            request.args.get("status") or None,
            request.args.get("interview_status") or None,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"applications": [_application_json(item) for item in applications]})


@bp.post("/admin/applications/<int:application_id>/interview")
def admin_schedule_interview(application_id: int):
    admin = _require_admin()
    try:
        updated = _services()["applications"].schedule_interview(
            application_id,
            admin,
            request.form.get("contact_method", ""),
            request.form.get("preferred_times", ""),
            request.form.get("interviewer", ""),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if not updated:
        abort(404)
    return jsonify({"status": "scheduled"})


@bp.route(
    "/admin/applications/<int:application_id>/interview-notes",
    methods=["GET", "POST"],
)
def admin_interview_notes(application_id: int):
    username = _require_login()
    if request.method == "POST":
        try:
            note = _services()["applications"].add_interview_note(
                application_id,
                username,
                request.form.get("category", ""),
                request.form.get("content", ""),
            )
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except PermissionError:
            abort(403)
        return jsonify({"id": note.id, "category": note.category}), 201
    try:
        notes = _services()["applications"].list_interview_notes(
            application_id, username
        )
    except PermissionError:
        abort(403)
    return jsonify(
        {
            "notes": [
                {
                    "id": note.id,
                    "category": note.category,
                    "author_username": note.author_username,
                    "content": note.content,
                    "created_at": note.created_at,
                }
                for note in notes
            ]
        }
    )


@bp.post("/chatting")
def chat():
    sender = _require_login()
    _limit("chat", 60, 60)
    content = request.form.get("message", "").strip()
    receiver = request.form.get("receiver", "").strip()
    if not content or not receiver:
        return render_template(
            "error.html", message="Message and receiver are required"
        ), 400
    upload = request.files.get("chat_image")
    attachment = None
    if upload and upload.filename:
        try:
            attachment = _services()["uploads"].save_image(upload)
        except ValueError as error:
            return render_template("error.html", message=str(error)), 400
    attachment_data = vars(attachment) if attachment else None
    try:
        message = _services()["messages"].create(
            sender, receiver, content, attachment_data
        )
    except LookupError:
        if attachment:
            (Path(current_app.config["UPLOAD_DIR"]) / attachment.stored_name).unlink(
                missing_ok=True
            )
        return render_template("error.html", message="Receiver does not exist"), 404
    return render_template("chat_message.html", message=message, attachment=attachment)


@bp.get("/uploads/<path:stored_name>")
def uploaded_file(stored_name: str):
    username = _require_login()
    if not _services()["messages"].can_access_attachment(stored_name, username):
        abort(404)
    return send_from_directory(Path(current_app.config["UPLOAD_DIR"]), stored_name)


@bp.post("/posts")
def create_post():
    author = _require_login()
    _limit("post", 20, 60)
    content = request.form.get("content", "").strip()
    if not content:
        abort(400)
    _services()["posts"].create(author, content)
    return redirect(url_for("hanger.index"))


@bp.post("/posts/<int:post_id>/comments")
def comment(post_id: int):
    author = _require_login()
    content = request.form.get("content", "").strip()
    if not content:
        abort(400)
    if not _services()["posts"].comment(post_id, author, content):
        abort(404)
    return redirect(url_for("hanger.index"))


@bp.post("/posts/<int:post_id>/likes")
def like(post_id: int):
    result = _services()["posts"].like(post_id, _require_login())
    if result is None:
        abort(404)
    if result is False:
        abort(409)
    return redirect(url_for("hanger.index"))
