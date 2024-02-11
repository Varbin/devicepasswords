# SPDX-License-Identifier: MPL-2.0
"""
Implementation of Dovecot's hashes variants.

The format is:

{SCRAM-SHA-bits},rounds,base64(salt),base64(stored_key),base64(server_key)
"""
import hmac
from base64 import b64encode, b64decode
from secrets import token_bytes
from typing import Literal

import hashlib

from passlib.hash import scram
from passlib.utils.handlers import GenericHandler
from passlib.ifc import PasswordHash

ROUNDS = 200_000
CLIENT_KEY = b"Client Key"
SERVER_KEY = b"Server Key"


def _dovecot_scram(password: str, alg: Literal["sha-1", "sha-256", "sha-512"],
                   salt: bytes|None = None, rounds: int = ROUNDS) -> str:
    if salt is None:
        salt = token_bytes(16)
    digest = scram.derive_digest(password, salt, rounds, alg)
    serverkey = hmac.digest(digest, SERVER_KEY, alg)
    clientkey = hmac.digest(digest, CLIENT_KEY, alg)
    storedkey = hashlib.new(alg, clientkey, usedforsecurity=True).digest()

    return ",".join((
        f"{{SCRAM-{alg.upper()}}}{rounds}",
        b64encode(salt).decode(),
        b64encode(storedkey).decode(),
        b64encode(serverkey).decode()
    ))


class DovecotSCRAMSHA256(GenericHandler):
    name = "dovecot_scram_sha256"
    _algorithm = "sha-256"
    setting_kwds = ("rounds", "salt")

    @classmethod
    def hash(cls, secret, **setting_and_context_kwds):
        return _dovecot_scram(secret, cls._algorithm,
                              **setting_and_context_kwds)

    @classmethod
    def verify(cls, secret, hash, **context_kwds):
        if not cls.identify(hash):
            return False

        rounds, salt, _, _ = hash.split(",")
        try:
            rounds = int(rounds[len(f"{{SCRAM-{cls._algorithm}}}"):])
        except ValueError:
            return False
        digest = cls.hash(secret, salt=b64decode(salt), rounds=rounds)
        print(digest)
        return hmac.compare_digest(digest, hash)

    @classmethod
    def using(cls, relaxed=False, **kwds):
        return cls()

    @classmethod
    def identify(cls, hash):
        return hash.startswith(f"{{SCRAM-{cls._algorithm.upper()}}}")


class DovecotSCRAMSHA1(DovecotSCRAMSHA256):
    name = "dovecot_scram_sha1"
    _algorithm = "sha-1"
