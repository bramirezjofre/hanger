import hmac
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


def _require_admin() -> None:
    supplied = request.headers.get("X-Admin-Token", "")
    expected = current_app.config["ADMIN_TOKEN"]
    if not supplied or not hmac.compare_digest(supplied, expected):
        abort(403)


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
        return render_template("register.html")
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
    _require_admin()
    if request.method == "POST":
        try:
            _services()["invitations"].invite(
                request.form.get("contact_address", ""),
                request.form.get("contact_kind", ""),
                f"{current_app.config['PUBLIC_URL']}/register",
            )
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
    return jsonify({"invitations": _services()["invitation_repository"].list_all()})


@bp.post("/chatting")
def chat():
    sender = _require_login()
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
    except Exception:
        if attachment:
            (Path(current_app.config["UPLOAD_DIR"]) / attachment.stored_name).unlink(
                missing_ok=True
            )
        raise
    return render_template("chat_message.html", message=message, attachment=attachment)


@bp.get("/uploads/<path:stored_name>")
def uploaded_file(stored_name: str):
    _require_login()
    return send_from_directory(Path(current_app.config["UPLOAD_DIR"]), stored_name)


@bp.post("/posts")
def create_post():
    author = _require_login()
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
    _services()["posts"].comment(post_id, author, content)
    return redirect(url_for("hanger.index"))


@bp.post("/posts/<int:post_id>/likes")
def like(post_id: int):
    _services()["posts"].like(post_id, _require_login())
    return redirect(url_for("hanger.index"))
