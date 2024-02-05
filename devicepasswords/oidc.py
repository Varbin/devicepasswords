# SPDX-License-Identifier: MPL-2.0
"""
OIDC implementation.
"""
import _thread
import asyncio
import logging
import sys
import time
from collections import namedtuple
from urllib.parse import urlparse, parse_qs, urlencode

import aiohttp
from flask import Flask, current_app, g
from jose import JWTError
from jose import jwt, jwk
from jose.exceptions import JWTClaimsError, ExpiredSignatureError, JWKError

Redeemed = namedtuple('Redeemed', ['id_token', 'expires_in',
                                   'refresh_token', 'refresh_token_expires_in',
                                   'claims', 'profile']
                      )


class OIDC:
    """OpenID Connect implementation.

    This implementation is bound to flask and a running flask app.
    """
    _refresh = False

    keys = []
    config = {}

    configuration_url: str
    client_id: str
    client_secret: str

    @property
    def session(self):
        """Return a session for the current request."""
        if 'aiohttp_session' not in g:
            g.aiohttp_session = aiohttp.ClientSession()

        return g.aiohttp_session

    @property
    def refresh(self):
        """Enable continuous background refresh."""
        return self._refresh

    @refresh.setter
    def refresh(self, new_bool):
        if not self._refresh and new_bool:
            _thread.start_new_thread(self._refresh_config, (), {})

        self._refresh = new_bool

    @property
    def supports_frontchannel_logout(self):
        """Check if frontchannel logout is supported."""
        return self.config.get("http_logout_supported") or \
            self.config.get("frontchannel_logout_supported")

    async def refresh_config(self) -> dict:
        """Refresh the configuration from the OIDC provider."""
        async with aiohttp.request('GET', self.configuration_url) as response:
            response.raise_for_status()
            config = await response.json()
            self.config = config
            return config

    async def refresh_keys(self):
        """Refresh the configuration from the OIDC provider.

        :raise ExceptionGroup of JWK errors, or a value error.
        """
        async with aiohttp.request('get', self.config["jwks_uri"]) as response:
            response.raise_for_status()
            self.set_keys(await response.json())

    def set_keys(self, obj):
        """Update the keys of the OIDC provider"""
        keys = []
        exceptions = []
        certs = obj["keys"]
        # There can be unusable keys here
        verifying = filter(
            lambda k:
            k["alg"] != "RSA-OAEP" and
            k.get("use", "sig") == "sig" and
            "verify" in k.get("key_ops", ["verify"]),
            certs
        )
        for cert in verifying:
            try:
                key = jwk.construct(cert)
            except JWKError as e:
                exceptions.append(e)
            else:
                keys.append((cert.get("kid", ""), key))
        if not keys and exceptions:
            raise ExceptionGroup("Cannot decode any jwk!", exceptions)
        if not keys:
            raise ValueError("No keys found!")
        self.keys = keys
        return keys

    def _refresh_config(self):
        while self._refresh:
            time.sleep(3600)

            try:
                _ = asyncio.run(self.refresh_config())
            except:  # noqa: E722
                logging.getLogger(__name__).error("Cannot refresh config.",
                                                  exc_info=sys.exc_info())

            try:
                _ = asyncio.run(self.refresh_keys())
            except:  # noqa: E722
                logging.getLogger(__name__).error("Cannot refresh keys.",
                                                  exc_info=sys.exc_info())

    async def _redeem(self, token_data) -> tuple[Redeemed, Exception | None]:
        auth = None
        if not self.client_secret:
            token_data["client_id"] = self.client_id
        elif "client_secret_post" not in \
                self.config.get("token_endpoint_auth_methods_supported", ()):
            token_data["client_id"] = self.client_id
            auth = (self.client_id, self.client_secret)
        else:
            token_data["client_id"] = self.client_id
            token_data["client_secret"] = self.client_secret

        token_response = await self.session.post(self.config["token_endpoint"],
                                                 data=token_data, auth=auth)
        try:
            token_response.raise_for_status()
        except IOError as e:
            return Redeemed(None, 0, None, 0, {}, {}), e
        token_json = await token_response.json()

        claims, e = self.validate_token(
            token_json["id_token"],
            token_json.get("access_token")
        )

        if e is not None:
            return Redeemed(None, 0, None, 0, {}, {}), e

        profile = {}
        if at := token_json.get("access_token"):
            profile = await (await self.session.get(
                self.config["userinfo_endpoint"],
                headers={"Authorization": f"Bearer {at}"}
            )).json()

        return Redeemed(
            token_json["id_token"],
            token_json.get("expires_in", 0),
            token_json.get("refresh_token"),
            token_json.get("refresh_expires_in"),
            claims, profile
        ), None

    async def redeem_refresh(self, code) -> tuple[Redeemed, Exception | None]:
        """Redeem a refresh token to claims and userinfo."""
        return await self._redeem({
            "grant_type": "refresh_token",
            "refresh_token": code,
            "scope": "openid email profile",
        })

    async def redeem_code(self, code, redirect_uri) -> \
            tuple[Redeemed, Exception | None]:
        """Redeem an access token to claims and userinfo."""
        return await self._redeem({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        })

    def get_login_uri(self, state, redirect_uri) -> str:
        """Return the redirect URL to sign in."""

        auth_url = urlparse(self.config["authorization_endpoint"])
        query = parse_qs(auth_url.query, strict_parsing=True, separator="&") \
            if auth_url.query else dict()
        query["state"] = state
        query["response_type"] = "code"
        query["scope"] = "openid email profile"
        query["redirect_uri"] = redirect_uri
        query["client_id"] = self.client_id
        if "form_post" in self.config.get("response_modes_supported", ()):
            query["response_mode"] = "form_post"
        # else:
        #    query["response_mode"] = "query"
        return auth_url._replace(query=urlencode(query)).geturl()

    def get_logout_url(self, id_token, email, post_logout) -> str | None:
        """
        Return a logout url for an id token and an email address as a
        logout hint.
        """
        if not (endpoint := self.config.get("end_session_endpoint")):
            return None

        endpoint_url = urlparse(endpoint)
        query = parse_qs(endpoint_url.query, strict_parsing=True,
                         separator="&") \
            if endpoint_url.query else dict()
        query["id_token_hint"] = id_token
        query["logout_hint"] = email
        query["client_id"] = self.client_id
        query["post_logout_redirect_uri"] = post_logout
        return endpoint_url._replace(query=urlencode(query)).geturl()

    def validate_token(self, token: str, at: str | None = None, typ="ID") -> \
            tuple[dict | None, Exception | None]:
        """Validate an open id connect token."""
        exceptions = []
        for (kid, key) in self.keys:
            try:
                claims = jwt.decode(
                    token,
                    key,
                    audience=self.client_id,
                    access_token=at,
                    issuer=self.config["issuer"]
                )
                break
            except (JWTError, JWTClaimsError, ExpiredSignatureError) as e:
                exceptions.append(e)
        else:
            return None, ExceptionGroup("Cannot decode token", exceptions)

        logging.getLogger(__name__).info("Got %s token for %s signed by %s" % (
            claims.get("typ", "ID"), claims.get("sub", "-"), kid,
        ))

        if not claims.get("typ", "ID") == typ:
            return None, ValueError("Invalid type: %s" % claims["typ"])

        return claims, None

    def init_app(self, app: Flask) -> None:
        self.configuration_url = app.config["OIDC_DISCOVERY_URL"]
        self.client_id = app.config["OIDC_CLIENT_ID"]
        self.client_secret = app.config["OIDC_CLIENT_SECRET"]

        app.teardown_request(self._teardown)

    async def _teardown(self, request):
        if session := g.pop("aiohttp_session", None):
            await session.close()




oidc = OIDC()
