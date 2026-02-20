"""
WSGI entry point for production deployment.
This file is used by Gunicorn to start the application.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
