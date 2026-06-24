#!/usr/bin/bash
# Go to Repository Source Code root
cd /workspaces/hanger/src/
# Create Isolated Enviroment
python3 -m venv .venv
source .venv/bin/activate
pip3 install poetry==2.2.1
poetry install -E dev
# Run App
poetry run flask --app hanger_app:create_app run --debug
poetry run flask --app hanger_app:create_app process-jobs --watch