# SPDX-License-Identifier: MPL-2.0
"""
Device password manager.

@author Varbin the Fox.
"""
import http
import json
import secrets
import sys
import time
import uuid
from datetime import date, timedelta, datetime

from flask import Flask, session, redirect, render_template, request, \
    url_for, abort
from sqlalchemy import Uuid

from .db import db, init_db, Session, User, Token
from .devpwd import DevicePasswords
from .oidc import OIDC
from .pwdhash import hasher
from .smgmt import valid_session, update_session, destroy_session, \
    new_session


def create_app():
    """
    Return the app instance.

    :return: WSGI compatible instance
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config["WORDLIST"] = "wordlist.txt"
    app.config["OIDC_CLAIM_EMAIL"] = "email"
    app.config["OIDC_CLAIM_EMAIL_VERIFIED"] = "email_verified"
    app.config["OIDC_CLAIM_USERNAME"] = "preferred_username"
    app.config["OIDC_SCOPE"] = "openid email profile"
    app.config["PASSWORD_HASH"] = "plaintext"
    app.config["PASSWORD_MAX_EXPIRATION_DAYS"] = 0
    app.config["PASSWORD_ENTROPY"] = 64
    app.config["UI_HEADING"] = "Device passwords"
    app.config["UI_HEADING_SUB"] = ""
    app.config["UI_SHOW_SUBJECT"] = True
    app.config["UI_SHOW_LAST_USED"] = True
    app.config["UI_NO_AWOO"] = False

    app.config.from_prefixed_env("DP")

    for var in ["OIDC_DISCOVERY_URL", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET",
                "SQLALCHEMY_DATABASE_URI"]:
        if not app.config.get(var):
            app.logger.error(f"{var} not set.")
            exit(1)

    try:
        hasher.hash("", scheme=app.config["PASSWORD_HASH"])
    except KeyError:
        app.logger.error(
            f"Invalid password hash {app.config['PASSWORD_HASH']}",
            exc_info=sys.exc_info()
        )
        exit(1)

    try:
        int(app.config["PASSWORD_MAX_EXPIRATION_DAYS"])
    except TypeError:
        app.logger.error(
            f"Invalid expiration date value " +
            app.config['PASSWORD_MAX_EXPIRATION_DAYS'],
            exc_info=sys.exc_info()
        )
        exit(1)

    if not app.config.get("SECRET_KEY"):
        app.logger.warning("No secret key set, generating a fresh one. "
                           "Set one for a load balanced setup.")
        app.config["SECRET_KEY"] = secrets.token_bytes(32)

    init_db(app)

    oidc = OIDC.from_app(app)
    for i in range(5):
        time.sleep(2**i-1)
        try:
            oidc.refresh_config()
        except:
            app.logger.warning(f"Cannot connect to IdP (try {i+1}/5)",
                               exc_info=sys.exc_info())
        else:
            break
    else:
        app.logger.error("Cannot connect to IdP try (5/5).")
    # Manual overwriting keys here
    # Some IdPs may have different keys for consumer and business accounts,
    # and Oracle ICS instances would need authentication.
    if keyfile := app.config.get("OIDC_CERTS"):
        with open(keyfile) as kf:
            oidc.set_keys(json.load(kf))
    else:
        oidc.refresh_keys()
    oidc.refresh = True  # Automatically reload in background.
    device_passwords = DevicePasswords.from_app(app)

    @app.route("/")
    def index():
        """Render the web interface or login."""
        if not valid_session(oidc):
            session.clear()
            session["state"] = secrets.token_urlsafe(16)
            return redirect(oidc.get_login_uri(
                session["state"], url_for("login", _external=True)
            ))

        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Handle OpenID connect responses."""
        if request.method == "GET":
            args = request.args
        else:
            args = request.form

        if session.get("state") != args.get("state"):
            abort(400)

        if not (code := args.get("code")):
            abort(400)

        redeemed, e = oidc.redeem_code(
            code, url_for("login", _external=True)
        )
        if e is not None:
            app.logger.error("Cannot redeem code.", exc_info=(
                type(e), e, e.__traceback__
            ))
            if isinstance(e, IOError):
                abort(http.HTTPStatus.BAD_GATEWAY)
            abort(400)

        new_session(redeemed)

        app.logger.info(
            "User %s logged in (sub=%s, username=%s, sid=%s)",
            session["email"],
            session["sub"],
            session["preferred_username"],
            session.get("sid", "-")
        )

        user = db.session.get(User, session["sub"]) or User(sub=session["sub"])
        user.username = session["preferred_username"]
        user.email = session["email"]
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        """Clear the session."""
        if session.get("state") != request.args.get("state"):
            app.logger.warning("Invalid session.")
            abort(403)

        app.logger.warning("%s logged out", session["email"])

        token = session["token"]
        email = session["email"]

        if sid := session.get("sid"):
            destroy_session(None, sid)

        if logout_url := oidc.get_logout_url(
                token, email, url_for("index", _external=True)
        ):
            return redirect(logout_url)

        return redirect(url_for("index"))

    @app.route("/api/ping")
    def ping():
        return {"pong": valid_session(oidc)}

    @app.route("/api/logout-frontchannel")
    def frontchannel_logout():
        """
        Implement a 'front channel' logout that is initiated on the IdP page.
        Is only active, if the IdP supports it.
        """

        # Old standard:
        # https://openid.net/specs/openid-connect-logout-1_0-04.html
        # New standard:
        # https://openid.net/specs/openid-connect-frontchannel-1_0.html
        # That is why there are to variables ^^
        if (not oidc.config.get("http_logout_supported") and
                not oidc.config.get("frontchannel_logout_supported")):
            return abort(400, "Feature not supported.")

        sid = request.args.get("sid")
        iss = request.args.get("iss")

        if (oidc.config.get("logout_session_supported") or
                oidc.config.get("frontchannel_logout_session_supported")):
            if not sid or not iss:
                return abort(400, "Missing session")

        if iss and sid:
            if iss != oidc.config.get("iss"):
                return abort(400, "Invalid issuer.")
            destroy_session(None, sid)
        else:
            if sid := session.get("sid"):
                destroy_session(None, sid)
            else:
                session.clear()

        return ""


    @app.route("/api/logout-backchannel", methods=["POST"])
    def backchannel_logout():
        """
        Implement a 'back channel' logout that can be called by the
        IdP on user logout.
        """
        if not (token := request.form.get("logout_token")):
            abort(400)

        claims, e = oidc.validate_token(token, typ="Logout")
        if e is not None:
            app.logger.error("Cannot validate logout token", exc_info=(
                type(e), e, e.__traceback__
            ))
            app.logger.info("Cannot validate logout token.")
            abort(400)

        if claims.get("events", {}).get(
                "http://schemas.openid.net/event/backchannel-logout") is None:
            app.logger.info("No logout event.")
            abort(400)
        if claims.get("nonce"):
            app.logger.info("Nonce present.")
            abort(400)
        # We skip a bit here, as we only support a single IdP
        sid = claims.get("sid")
        sub = claims.get("sub")
        if not sid and not sub:
            app.logger.info("Sid or sub not present")
            abort(400)

        app.logger.info("Backchannel logout (sid=%s, sub=%s)",
                        sid or '-', sub or '-')

        destroy_session(sub, sid)
        return ""

    @app.route("/api/tokens", methods=["GET", "POST", "DELETE"])
    def tokens():
        """Token endpoint."""
        if not valid_session(oidc):
            app.logger.warning("Invalid session.")
            session.clear()
            abort(403)

        match request.method:
            case "GET":
                user_tokens = db.session.execute(
                    db.select(Token)
                    .filter_by(sub=session["sub"])
                ).scalars() or []
                return [
                    {
                        "id": token.id,
                        "name": token.name,
                        "expires": token.expires,
                    } for token in user_tokens
                ]

            case "POST":
                if request.form.get("state") != session["state"]:
                    app.logger.warning("Invalid CSRF token")
                    abort(403)

                if not (name := request.form.get("name")):
                    abort(400)
                if expires := request.form.get("expire"):
                    expires = date.fromisoformat(expires)
                else:
                    expires = None
                if ((expiration := app.config["PASSWORD_MAX_EXPIRATION_DAYS"])
                        > 0):
                    maximum = ((datetime.now() + timedelta(days=expiration))
                               .date())
                    if expires is None or expires > maximum:
                        expires = maximum

                token_value = device_passwords.generate()
                t = Token(
                    sub=session["sub"],
                    name=name,
                    token=hasher.hash(token_value,
                                      scheme=app.config["PASSWORD_HASH"]),
                    expires=expires
                )
                db.session.add(t)
                db.session.commit()
                return {
                    "status": "ok",
                    "name": name,
                    "secret": token_value,
                }

            case "DELETE":
                token = db.session.execute(
                    db.select(Token)
                    .filter_by(
                        sub=session["sub"],
                        id=request.form.get("id"))
                ).scalar_one_or_none()
                if token is None:
                    abort(404)
                db.session.delete(token)
                db.session.commit()
                return {
                    "id": token.id,
                    "name": token.name,
                }
            case _:
                abort(400)

    return app
