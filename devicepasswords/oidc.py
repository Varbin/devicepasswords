import base64
import secrets
import sys
import time
from collections import namedtuple
from urllib.parse import urlparse, parse_qs, urlencode

import _thread
import requests
from flask import Flask

from jose import jwt, jwk
from jose import JWTError
from jose.exceptions import JWTClaimsError, ExpiredSignatureError, JWKError


import logging

Redeemed = namedtuple('Redeemed', ['id_token', 'expires_in',
                                   'refresh_token', 'refresh_token_expires_in',
                                   'claims']
                      )


class OIDC:
    """OpenID Connect implementation."""
    _refresh = False

    keys = []
    config = {}

    def __init__(self, configuration_url: str, client_id: str, client_secret: str):
        self.configuration_url = configuration_url
        self.client_id = client_id
        self.client_secret = client_secret

        self.session = requests.Session()

        self.refresh_config()
        self.refresh_keys()

    @property
    def refresh(self):
        return self._refresh

    @refresh.setter
    def refresh(self, new_bool):
        if not self._refresh and new_bool:
            _thread.start_new_thread(self._refresh_config, (), {})

        self._refresh = new_bool

    def refresh_config(self) -> dict:
        """Refresh the configuration from the OIDC provider."""
        response = self.session.get(self.configuration_url)
        response.raise_for_status()
        config = response.json()
        self.config = config
        return config

    def refresh_keys(self) -> list:
        """Refresh the configuration from the OIDC provider.

        :raise ExceptionGroup of JWK errors, or a value error.
        """
        keys = []
        exceptions = []
        cert_response = self.session.get(self.config["jwks_uri"])
        cert_response.raise_for_status()
        certs = cert_response.json()["keys"]
        for cert in certs:
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
                _ = self.refresh_config()
            except:
                logging.getLogger(__name__).error("Cannot refresh config.",
                                                  exc_info=sys.exc_info())

            try:
                _ = self.refresh_keys()
            except:
                logging.getLogger(__name__).error("Cannot refresh keys.",
                                                  exc_info=sys.exc_info())

    def _redeem(self, token_data) -> tuple[Redeemed, Exception | None]:
        auth = ()
        if not self.client_secret:
            token_data["client_id"] = self.client_id
        elif "client_secret_post" not in \
                 self.config.get("token_endpoint_auth_methods_supported", ()):
            token_data["client_id"] = self.client_id
            auth = (self.client_id, self.client_secret)
        else:
            token_data["client_id"] = self.client_id
            token_data["client_secret"] = self.client_secret

        token_response = self.session.post(self.config["token_endpoint"],
                                           data=token_data, auth=auth)
        try:
            token_response.raise_for_status()
        except IOError as e:
            return Redeemed(None, 0, None, 0, {}), e
        token_json = token_response.json()

        claims, e = self.validate_token(
            token_json["id_token"],
            token_json.get("access_token")
        )

        if e is not None:
            return Redeemed(None, 0, None, 0, {}), e

        return Redeemed(
            token_json["id_token"],
            token_json.get("expires_in", 0),
            token_json.get("refresh_token"),
            token_json.get("refresh_expires_in"),
            claims
        ), None

    def redeem_refresh(self, code) -> tuple[Redeemed, Exception | None]:
        return self._redeem({
            "grant_type": "refresh_token",
            "refresh_token": code,
            "scope": "openid email profile",
        })

    def redeem_code(self, code, redirect_uri) -> \
            tuple[Redeemed, Exception | None]:
        return self._redeem({
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
        else:
            query["response_mode"] = "query"
        return auth_url._replace(query=urlencode(query)).geturl()

    def get_logout_url(self, id_token, email, post_logout) -> str|None:
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

    @classmethod
    def from_app(cls, app: Flask):
        return cls(
            app.config["OIDC_DISCOVERY_URL"],
            app.config["OIDC_CLIENT_ID"],
            app.config["OIDC_CLIENT_SECRET"]
        )