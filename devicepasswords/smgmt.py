# SPDX-License-Identifier: MPL-2.0
"""
Session management.
"""
import logging
import secrets
import time
from datetime import datetime, timedelta

from flask import current_app, abort, session

from . import OIDC
from .db import db, Session
from .oidc import Redeemed

logger = logging.getLogger(__name__)


def valid_session(oidc: OIDC) -> bool:
    """Return if a session is valid."""
    if not session.get("sub"):
        return False

    expired = session.get("exp", 0) < time.time()

    if not (sid := session.get("sid")):
        return not expired

    # Session not in database
    if (sinfo := db.session.get(Session, sid)) is None:
        return False
    if not expired:
        return True

    # Session is expired and cannot be refreshed in any way.
    if expired and (not sinfo.refresh_token or (
            sinfo.refresh_token_expiration is not None and
            sinfo.refresh_token_expiration < datetime.now()
    )):
        return False

    current_app.logger.info("Refreshing session (sid=%s)" % sid)
    redeemed, e = oidc.redeem_refresh(sinfo.refresh_token)
    if e is not None:
        current_app.logger.warning(
            "Refreshing failed (sid=%s)" % sid,
            exc_info=(type(e), e, e.__traceback__)
        )
        destroy_session(sid=sid)
        return False

    current_app.logger.info("Refreshing successful (sid=%s)" % sid)

    sinfo.id_token = redeemed.id_token
    sinfo.refresh_token = redeemed.refresh_token
    if redeemed.expires_in:
        sinfo.refresh_token_expiration = (
                datetime.now() +
                timedelta(seconds=redeemed.refresh_token_expires_in)
        )
    else:
        sinfo.refresh_token_expiration = None

    update_session(redeemed.id_token, redeemed.claims, redeemed.profile)
    db.session.add(sinfo)
    db.session.commit()

    return True


def destroy_session(sub=None, sid=None):
    session.clear()

    if sid:
        if (sess := db.session.get(Session, sid)) is not None:
            db.session.delete(sess)
    elif sub:
        for sess in db.session.execute(
                db.select(Session).filter_by(sub=sub)
        ).scalars() or []:
            db.session.delete(sess)

    db.session.commit()


def new_session(redeemed: Redeemed):
    session.clear()
    session["state"] = secrets.token_urlsafe(16)

    update_session(redeemed.id_token, redeemed.claims, redeemed.profile)
    if not (sid := redeemed.claims.get("sid")):
        return
    sess = db.session.get(Session, sid) or Session(sid=sid)
    sess.sub = redeemed.claims.get("sub")
    sess.id_token = redeemed.id_token
    sess.refresh_token = redeemed.refresh_token
    if redeemed.refresh_token_expires_in:
        sess.refresh_token_expiration = datetime.now() + \
                                        timedelta(
                                            seconds=redeemed.refresh_token_expires_in)

    db.session.add(sess)
    db.session.commit()


def update_session(id_token, claims, profile):
    """Update the id_token and the claims of the current message."""
    app = current_app

    session["token"] = id_token

    required = [
        "sub", app.config["OIDC_CLAIM_EMAIL"],
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

    # Always present (more or less)
    for claim in ["exp", "iss"]:
        session[claim] = claims[claim]

    session["sub"] = claims["sub"]
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
