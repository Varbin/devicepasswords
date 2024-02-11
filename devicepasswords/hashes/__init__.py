# SPDX-License-Identifier: MPL-2.0
"""
Custom password hashes for specific applications.

All hashes are registered into the passlib registry.
"""

from .dovecot import DovecotSCRAMSHA1, DovecotSCRAMSHA256


from passlib.registry import register_crypt_handler

register_crypt_handler(DovecotSCRAMSHA1)
register_crypt_handler(DovecotSCRAMSHA256)
