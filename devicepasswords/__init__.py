import http
import secrets
import sys
import time
import traceback
from datetime import datetime, date

import requests.exceptions
from flask import Flask, session, redirect, render_template, request, \
    url_for, abort, current_app

from .db import db, init_db, Session, User, Token
from .devpwd import DevicePasswords
from .oidc import OIDC
from .smgmt import valid_session, update_session, destroy_session, \
    new_session


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["WORDLIST"] = "wordlist.txt"
    app.config["OIDC_CLAIM_EMAIL"] = "email"
    app.config["OIDC_CLAIM_EMAIL_VERIFIED"] = "email_verified"
    app.config["OIDC_CLAIM_USERNAME"] = "preferred_username"
    app.config["OIDC_SCOPE"] = "openid email profile"

    app.config.from_prefixed_env("DP")

    for var in ["OIDC_DISCOVERY_URL", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET",
                "SQLALCHEMY_DATABASE_URI"]:
        if not app.config.get(var):
            print(f"{var} not set.", file=sys.stderr)
            exit(1)

    if not app.config.get("SECRET_KEY"):
        print("No secret key set, generating a fresh one. "
              "Set one for a load balanced setup.")
        app.config["SECRET_KEY"] = secrets.token_bytes(32)

    init_db(app)

    oidc = OIDC.from_app(app)
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

        user = db.session.get(User, session["sub"]) or User(
            primary=session["sub"])
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
        session.clear()

        if logout_url := oidc.get_logout_url(
                token, email, url_for("index", _external=True)
        ):
            return redirect(logout_url)

        return redirect(url_for("index"))

    @app.route("/api/ping")
    def ping():
        return {"pong": valid_session(oidc)}

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
                    .filter_by(user=session["sub"])
                ).scalars() or []
                return [
                    {
                        "primary": token.primary,
                        "name": token.name,
                        "expires": token.expires,
                    } for token in user_tokens
                ]

            case "POST":
                if request.form.get("state") != session["state"]:
                    print(request.form.get("state"), session["state"])
                    app.logger.warning("Invalid CSRF token")
                    abort(403)

                if not (name := request.form.get("name")):
                    abort(400)
                if expires := request.form.get("expires"):
                    expires = date.fromisoformat(expires)
                else:
                    expires = None

                token_value = device_passwords.generate()
                t = Token(
                    user=session["sub"],
                    name=name,
                    token=token_value,
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
                        user=session["sub"],
                        primary=request.form.get("id"))
                ).scalar_one_or_none()
                if token is None:
                    abort(404)
                db.session.delete(token)
                db.session.commit()
                return {
                    "primary": token.primary,
                    "name": token.name,
                }
            case _:
                abort(400)

    return app