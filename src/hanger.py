#!/usr/bin/python3
import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, session

import base.interviewer
import base.user


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = PROJECT_ROOT / "pages"

web = Flask(__name__)
web.config["SECRET_KEY"] = os.environ.get("HANGER_SECRET_KEY", secrets.token_hex(32))

auth = base.interviewer.HangerSteps(
    os.environ.get("HANGER_DB_PATH", "registered_users.db")
)
users = [base.user.Profile(), base.user.Profile(), base.user.Profile()]
invited_contacts: list[str] = []


@web.get("/")
def main():
    return send_from_directory(PAGES_DIR, "hanger.html")


@web.post("/hanger-app")
def logged():
    username = request.form.get("hanger-user", "").strip()
    password = request.form.get("hanger-password", "")
    if not auth.login(username, password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["username"] = username
    return jsonify(auth.app.logged_user.get_data())


@web.get("/hangerSteps.html")
def registration_page():
    return send_from_directory(PAGES_DIR, "hangerSteps.html")


@web.post("/registered")
def register_ends():
    username = request.form.get("userName", "").strip()
    password = request.form.get("userPassword", "")
    confirmation = request.form.get("verifyPassword", "")
    if password != confirmation:
        return jsonify({"error": "Passwords do not match"}), 400

    try:
        created = auth.register(username, password)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if not created:
        return jsonify({"error": "Username already exists"}), 409
    return jsonify({"message": "User registered"}), 201


@web.post("/load")
def load_ends():
    contact = request.form.get("contact", "").strip()
    if not contact:
        return jsonify({"error": "Contact is required"}), 400
    if contact not in invited_contacts:
        invited_contacts.append(contact)
    return jsonify({"contacts": invited_contacts})


@web.get("/interviewer-report")
def make_report():
    return send_from_directory(PAGES_DIR, "loadUserForm.html")


@web.get("/hanger-steps")
def steps():
    return jsonify({"contacts": invited_contacts})


@web.post("/chatting")
def chat():
    username = session.get("username")
    if not username:
        return jsonify({"error": "Authentication required"}), 401

    sender = base.user.Profile()
    sender.name = username
    receiver = users[1]
    receiver.name = "Second"

    uploaded = request.files.get("chat-image")
    images = [Path(uploaded.filename).name] if uploaded and uploaded.filename else []

    chatter = base.user.HangerMessage()
    chatter.sender = sender
    chatter.receiver = receiver
    return chatter.send(request.form.get("message", ""), images)


@web.get("/pages/<path:asset>")
def pages(asset: str):
    return send_from_directory(PAGES_DIR, asset)


if __name__ == "__main__":
    web.run()
