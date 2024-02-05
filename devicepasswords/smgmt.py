# SPDX-License-Identifier: MPL-2.0
"""
Session management.
"""
import logging
import secrets
import time
from datetime import datetime, timedelta

from asgiref.sync import sync_to_async
from flask import current_app, abort, session

from .db import db, Revoked
from .oidc import Redeemed, OIDC

logger = logging.getLogger(__name__)


async def valid_session(oidc: OIDC) -> bool:
    """Return if a session is valid, refresh if short to expire."""
    if not session.get("sub"):
        return False

    valid_for = session.get("exp", 0) - time.time()
    if valid_for < 0:
        return False

    # Test if session was revoked by IdP
    if sid := session.get("sid"):
        if (await sync_to_async(db.session.get)(Revoked, sid)) is not None:
            return False

    if valid_for > 30:  # TODO: Make configurable
        return True

    if (not session.get("refresh_token") or (
        session.get("refresh_token_expiration") is not None and
        session.get("refresh_token_expiration") < datetime.now())):
        # Cannot refresh session, but is still valid.
        return True

    current_app.logger.info("Refreshing session (sid=%s)" % sid)
    redeemed, e = await oidc.redeem_refresh(session.get("refresh_token"))
    if e is not None:
        current_app.logger.warning(
            "Refreshing failed (sid=%s)" % sid,
            exc_info=(type(e), e, e.__traceback__)
        )
        await destroy_session(sid=sid)
        return False

    current_app.logger.info("Refreshing successful (sid=%s)" % sid)

    session["id_token"] = redeemed.id_token
    session["refresh_token"] = redeemed.refresh_token
    if redeemed.expires_in:
        session["refresh_token_expiration"] = (
                datetime.now() +
                timedelta(seconds=redeemed.refresh_token_expires_in)
        )
    else:
        session["refresh_token_expiration"] = None

    update_session(redeemed.id_token, redeemed.claims, redeemed.profile)

    return True


async def destroy_session(sub=None, sid=None):
    session.clear()

    if sid:
        db.session.add(Revoked(sid=sid))
        await sync_to_async(db.session.commit)()


def new_session(redeemed: Redeemed):
    session["state"] = secrets.token_urlsafe(16)
    session["id_token"] = redeemed.id_token
    session["refresh_token"] = redeemed.refresh_token
    session["sid"] = redeemed.claims.get("sid")
    if redeemed.refresh_token_expires_in:
        session["refresh_token_expiration"] \
            = (datetime.now() +
               timedelta(seconds=redeemed.refresh_token_expires_in))
    update_session(redeemed.id_token, redeemed.claims, redeemed.profile)


def update_session(id_token, claims, profile):
    """Update the id_token and the claims of the current message."""
    app = current_app

    session["token"] = id_token

    required = [
        "exp", "iss", "sub", app.config["OIDC_CLAIM_EMAIL"],
        app.config["OIDC_CLAIM_USERNAME"],
    ]
    if app.config.get("OIDC_CLAIM_VERIFIED"):
        required.append(app.config["OIDC_CLAIM_VERIFIED"])
    # Validate required claims:
    for claim in required:
        if not claims.get(claim) and not (
                app.config.get("OIDC_CLAIMS_FROM_PROFILE") and
                profile.get(claim)
        ):
            abort(403,
                  "Missing claim \"%s\". Contact your administrator."
                  % claim)

    # Always present
    for claim in ["exp", "sub"]:
        session[claim] = claims[claim]

    if claims.get("sid"):
        session["sid"] = claims["sid"]

    # Some IdPs only return the (for us mandatory data) in the profile.
    session["email"] = (claims.get(app.config["OIDC_CLAIM_EMAIL"]) or
                        profile.get(app.config["OIDC_CLAIM_EMAIL"]))
    session["preferred_username"] = (
        claims.get(app.config["OIDC_CLAIM_USERNAME"]) or
        profile.get(app.config["OIDC_CLAIM_USERNAME"])
    )
    # Not required, but useful.
    for claim in ["picture", "name"]:
        if claims.get(claim):
            # Will safely be loaded from profile
            session[claim] = claims[claim]
        elif profile.get(claim):
            session[claim] = profile[claim]

    if app.config.get("OIDC_CLAIM_VERIFIED"):
        if not claims.get(app.config["OIDC_CLAIM_VERIFIED"]):
            session.clear()
            abort(403, "Email not verified")
