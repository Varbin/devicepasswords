"""
Security headers for requests.
"""
import secrets
from urllib.parse import urlparse

from flask import Response, g, current_app
from .oidc import oidc


def add_nonce():
    g.nonce = secrets.token_urlsafe(16)


def add_security_headers(response: Response) -> Response:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        f"script-src 'nonce-{g.nonce}'; "
        f"style-src 'self'; "
        "img-src 'self' data: https:; connect-src 'self'; "
        "base-uri 'self'"
    )
    if oidc.supports_frontchannel_logout:
        # Assumption: There is only a single domain for the IdP
        parsed = urlparse(oidc.configuration_url)
        response.headers["Content-Security-Policy"] += \
            f"; frame-ancestors {parsed.scheme}://{parsed.netloc}"
    else:
        response.headers["Content-Security-Policy"] += \
            "; frame-ancestors 'none'"
        response.headers["X-Frame-Options"] = "DENY"

    if current_app.config["HSTS"]:
        response.headers["Strict-Transport-Security"] = "max-age=63072000"

    return response
