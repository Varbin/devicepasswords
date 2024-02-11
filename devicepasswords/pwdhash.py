# SPDX-License-Identifier: MPL-2.0
"""
Password hasher.
"""
from devicepasswords import hashes as _

from passlib.context import CryptContext


hasher = CryptContext([
    "plaintext",
    "hex_md5", "hex_sha1", "hex_sha256", "hex_sha512",
    "ldap_md5", "ldap_sha1", "ldap_salted_md5", "ldap_salted_sha1",
    "ldap_salted_sha256", "ldap_salted_sha512",
    "ldap_sha1_crypt", "ldap_sha256_crypt", "ldap_sha512_crypt",
    "ldap_bcrypt", "roundup_plaintext",
    "scram", "nthash",
    "bcrypt", "scrypt", "argon2",
    "md5_crypt", "sha1_crypt", "sha256_crypt", "sha512_crypt",
    # Custom implementations
    "dovecot_scram_sha1", "dovecot_scram_sha256"
])
