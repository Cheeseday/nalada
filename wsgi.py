"""WSGI entry point for production servers (gunicorn on Render).

Local development still launches via `create_app().run(...)` (see .claude/launch.json);
this module just exposes a ready-built `app` object so the production command can be
the conventional `gunicorn wsgi:app`.
"""
from app import create_app

app = create_app()
