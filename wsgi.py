"""
WSGI Entry Point
=================

This file is used by production servers (like Gunicorn) to run the app.
It's referenced in the Procfile for deployment.

You don't need to modify this file.
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
