# SPDX-License-Identifier: MPL-2.0
"""
Device password manager.

@author Varbin the Fox.
"""
import asyncio
import json
import sys
import time

from asgiref.sync import async_to_sync
from asgiref.wsgi import WsgiToAsgi
from flask import Flask
from flask_alembic import Alembic
from flask_session import Session

from .db import db
from .devpwd import device_passwords
from .headers import add_security_headers, add_nonce
from .oidc import oidc
from .pwdhash import hasher
from .views import views


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping({
        "HSTS": False,
        "WORDLIST": "wordlist.txt",
        "OIDC_CLAIM_EMAIL": "email",
        "OIDC_CLAIM_EMAIL_VERIFIED": "email_verified",
        "OIDC_CLAIM_USERNAME": "preferred_username",
        "OIDC_SCOPE": "openid email profile",
        "PASSWORD_HASH": "plaintext",
        "PASSWORD_MAX_EXPIRATION_DAYS": 0,
        "PASSWORD_ENTROPY": 64,
        "UI_HEADING": "Device passwords",
        "UI_HEADING_SUB": "",
        "UI_SHOW_SUBJECT": True,
        "UI_SHOW_LAST_USED": True,
        "UI_NO_AWOO": False,
        "UI_LOGINS": False,
        "SESSION_TYPE": "sqlalchemy",
        "SESSION_SQLALCHEMY": db,
        "DO_NOT_MIGRATE": False,
    })
    app.config.from_prefixed_env("DP")

    for var in ["OIDC_DISCOVERY_URL", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET",
                "SQLALCHEMY_DATABASE_URI"]:
        if not app.config.get(var):
            app.logger.error(f"DP_{var} not set.")
            raise ValueError(f"DP_{var} not set.")

    # Validate value of PASSWORD_HASH value
    try:
        hasher.hash("", scheme=app.config["PASSWORD_HASH"])
    except KeyError:
        app.logger.error(
            f"Invalid password hash {app.config['PASSWORD_HASH']}",
            exc_info=sys.exc_info()
        )
        raise

    # Validate PASSWORD_MAX_EXPIRATION_DAYS is an integer or can be casted to
    # one.
    try:
        int(app.config["PASSWORD_MAX_EXPIRATION_DAYS"])
    except TypeError:
        app.logger.error(
            "Invalid expiration date value " +
            app.config['PASSWORD_MAX_EXPIRATION_DAYS'],
            exc_info=sys.exc_info()
        )
        raise

    app.register_blueprint(views)
    db.init_app(app)
    create_all = db.create_all
    # Prevent automatic call create_all which kills alembic
    db.create_all = lambda bind_key=None: None
    Session(app)
    db.create_all = create_all
    # Required for Alembic, was removed in some flask-sqlalchemy version.
    app.extensions["sqlalchemy"].db = db
    alembic = Alembic(app)

    if not app.config["DO_NOT_MIGRATE"]:
        with app.app_context():
            alembic.upgrade()

    oidc.init_app(app)

    for i in range(5):
        time.sleep(2 ** i - 1)
        try:
            asyncio.run(oidc.refresh_config())
        except Exception as e:
            last = e
            app.logger.warning(f"Cannot connect to IdP (try {i + 1}/5)",
                               exc_info=sys.exc_info())
        else:
            break
    else:
        app.logger.error("Cannot connect to IdP try (5/5).")
        raise last

    # Manual overwriting keys here
    # Some IdPs may have different keys for consumer and business accounts,
    # and Oracle ICS instances would need authentication.
    if keyfile := app.config.get("OIDC_CERTS"):
        with open(keyfile) as kf:
            oidc.set_keys(json.load(kf))
    else:
        asyncio.run(oidc.refresh_keys())
    oidc.refresh = True  # Automatically reload in background.

    device_passwords.init_app(app)

    app.before_request(add_nonce)
    app.after_request(add_security_headers)

    return app


def create_asgi():
    return WsgiToAsgi(create_app())
