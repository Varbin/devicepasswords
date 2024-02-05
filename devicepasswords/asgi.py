"""
ASGI application.
"""

from asgiref.wsgi import WsgiToAsgi

from . import create_app as create_wsgi_app


def create_app() -> WsgiToAsgi:
    """Return an ASGI application."""
    return WsgiToAsgi(create_wsgi_app())
