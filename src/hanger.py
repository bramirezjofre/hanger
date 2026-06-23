#!/usr/bin/python3
from hanger_app import create_app

web = create_app()


if __name__ == "__main__":
    web.run()
