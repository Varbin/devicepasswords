import asyncio
import http
import secrets
import uuid

from datetime import datetime, date, timedelta

from asgiref.sync import sync_to_async
from flask import (request, redirect, render_template, url_for, session,
                   abort, current_app)
from flask.blueprints import Blueprint
from sqlalchemy import func

from . import device_passwords, oidc
from .db import db, User, Token
from .devpwd import DevicePasswords
from .pwdhash import hasher
from .smgmt import valid_session, new_session, destroy_session

views = Blueprint('views', __name__)


@views.route("/")
async def index():
    """Render the web interface or login."""
    if not (await valid_session(oidc)):
        session["state"] = secrets.token_urlsafe(16)
        return redirect(oidc.get_login_uri(
            session["state"], url_for("views.login", _external=True)
        ))

    return render_template("index.html")


@views.route("/login", methods=["GET", "POST"])
async def login():
    """Handle OpenID connect responses."""
    if request.method == "GET":
        args = request.args
    else:
        args = request.form

    if session.get("state") != args.get("state"):
        abort(400)

    if not (code := args.get("code")):
        abort(400)

    redeemed, e = await oidc.redeem_code(
        code, url_for("views.login", _external=True)
    )
    if e is not None:
        current_app.logger.error("Cannot redeem code.", exc_info=(
            type(e), e, e.__traceback__
        ))
        if isinstance(e, IOError):
            abort(http.HTTPStatus.BAD_GATEWAY)
        abort(400)

    new_session(redeemed)

    current_app.logger.info(
        "User %s logged in (sub=%s, username=%s, sid=%s)",
        session["email"],
        session["sub"],
        session["preferred_username"],
        session.get("sid", "-")
    )

    user = (await sync_to_async(db.session.get)(User, session["sub"])) or User(sub=session["sub"])
    user.username = session["preferred_username"]
    user.email = session["email"]
    db.session.add(user)
    await sync_to_async(db.session.commit)()

    return redirect(url_for("views.index"))


@views.route("/logout")
async def logout():
    """Clear the session."""
    if session.get("state") != request.args.get("state"):
        current_app.logger.warning("Invalid session.")
        abort(403)

    current_app.logger.warning("%s logged out", session["email"])

    token = session["token"]
    email = session["email"]

    if sid := session.get("sid"):
        await destroy_session(sid)
    else:
        session.clear()

    if logout_url := await oidc.get_logout_url(
            token, email, url_for("views.index", _external=True)
    ):
        return redirect(logout_url)

    return redirect(url_for("views.index"))


@views.route("/api/ping")
async def ping():
    """Return true if logged in."""
    return {"pong": await valid_session(oidc)}


@views.route("/api/logout-frontchannel")
async def frontchannel_logout():
    """
    Implement a 'front channel' logout that is initiated on the IdP page.
    Is only active if the IdP supports it.
    """

    # Old standard:
    # https://openid.net/specs/openid-connect-logout-1_0-04.html
    # New standard:
    # https://openid.net/specs/openid-connect-frontchannel-1_0.html
    # That is why there are to variables ^^
    if not oidc.supports_frontchannel_logout:
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
        await destroy_session(sid)
    elif sid:
        await destroy_session(sid)

    session.clear()

    return ""


@views.route("/api/logout-backchannel", methods=["POST"])
async def backchannel_logout():
    """
    Implement a 'back channel' logout that can be called by the
    IdP on user logout.
    """
    if not (token := request.form.get("logout_token")):
        abort(400)

    claims, e = oidc.validate_token(token, typ="Logout")
    if e is not None:
        current_app.logger.error("Cannot validate logout token", exc_info=(
            type(e), e, e.__traceback__
        ))
        current_app.logger.info("Cannot validate logout token.")
        abort(400)

    if claims.get("events", {}).get(
            "http://schemas.openid.net/event/backchannel-logout") is None:
        current_app.logger.info("No logout event.")
        abort(400)
    if claims.get("nonce"):
        current_app.logger.info("Nonce present.")
        abort(400)
    # We skip a bit here, as we only support a single IdP
    sid = claims.get("sid")
    sub = claims.get("sub")
    if not sid and not sub:
        current_app.logger.info("Sid or sub not present")
        abort(400)
    if not sid:
        current_app.logger.info("Sid not present (sub=%s)", sub)
        return ""

    current_app.logger.info("Backchannel logout (sid=%s, sub=%s)",
                    sid or '-', sub or '-')

    await destroy_session(sid)
    return ""


@views.route("/api/tokens", methods=["GET", "POST", "DELETE"])
async def tokens():
    """Token endpoint."""
    if not (await valid_session(oidc)):
        current_app.logger.warning("Invalid session.")
        session.clear()
        abort(403)

    match request.method:
        case "GET":
            user_tokens = (await sync_to_async(db.session.execute)(
                db.select(Token)
                .filter_by(sub=session["sub"])
            )).scalars() or []
            return [
                {
                    "id": token.id,
                    "name": token.name,
                    "expires": token.expires,
                } for token in user_tokens
            ]

        case "POST":
            if request.form.get("state") != session["state"]:
                current_app.logger.warning("Invalid CSRF token")
                abort(403)

            if not (name := request.form.get("name")):
                abort(400)
            if expires := request.form.get("expire"):
                expires = date.fromisoformat(expires)
            else:
                expires = None
            if ((expiration := current_app.config["PASSWORD_MAX_EXPIRATION_DAYS"])
                    > 0):
                maximum = ((datetime.now() + timedelta(days=expiration))
                           .date())
                if expires is None or expires > maximum:
                    expires = maximum

            token_value = device_passwords.generate()
            for _ in range(128):
                likely_unique = (
                    f"{session['preferred_username']}#"
                    f"{DevicePasswords.random_digits(3)}"
                )
                present = (await sync_to_async(db.session.execute)(
                    db.select(func.count())
                      .select_from(Token)
                      .filter_by(login=likely_unique))).scalar()
                if not present:
                    break
            else:
                return {
                    "status": "error",
                    "error": "Cannot create unique identifier",
                }

            t = Token(
                sub=session["sub"],
                name=name,
                token=hasher.hash(token_value,
                                  scheme=current_app.config["PASSWORD_HASH"]),
                expires=expires,
                login=likely_unique,
            )
            db.session.add(t)
            await sync_to_async(db.session.commit)()
            return {
                "status": "ok",
                "login": likely_unique,
                "name": name,
                "secret": token_value,
            }

        case "DELETE":
            token = (await sync_to_async(db.session.execute)(
                db.select(Token)
                .filter_by(
                    sub=session["sub"],
                    id=uuid.UUID(request.form.get("id")))
            )).scalar_one_or_none()
            if token is None:
                abort(404)
            db.session.delete(token)
            await sync_to_async(db.session.commit)()
            return {
                "id": token.id,
                "name": token.name,
            }
        case _:
            abort(400)
