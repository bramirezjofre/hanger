#!/usr/bin/python3
from hanger_app import create_app

# Backward-compatible Flask entry point. Interviewer routes now share the
# application factory and persistent services instead of module-level state.
loads = create_app()


if __name__ == "__main__":
    loads.run()
