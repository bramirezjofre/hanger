#!/usr/bin/python3
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import base.interviewer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = PROJECT_ROOT / "pages"

loads = Flask(__name__)
new_user = base.interviewer.loadUser()


@loads.route("/load", methods=["GET", "POST"])
def load_user():
    if request.method == "GET":
        return send_from_directory(PAGES_DIR, "loadUserForm.html")

    try:
        new_user.add_user(
            request.form.get("kind", ""), request.form.get("contact", "")
        )
        sent_to = new_user.send_steps()
    except (RuntimeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"sent_to": sent_to})


if __name__ == "__main__":
    loads.run()
