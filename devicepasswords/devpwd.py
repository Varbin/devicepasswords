# SPDX-License-Identifier: MPL-2.0
"""
Device password generation.
"""
import random

from flask import Flask

wordlist = []


class DevicePasswords:
    """Device password generator from list."""
    def __init__(self, words: list[str]):
        self.secure = random.SystemRandom()
        self.words = words

    def generate(self) -> str:
        """Generate device password consisting of 4 words and a 6-digit number,
        joined by dashes."""
        suffix = str(self.secure.randint(0, 99999)).rjust(5, '0')

        return "-".join(
            self.secure.choice(self.words).strip() for _ in range(4)
        ) + "-" + suffix

    @classmethod
    def from_app(cls, app: Flask):
        """Creates DevicePasswords instance from a Flask application where
        the config parameter WORDLIST is set to a line separated list of words.
        """
        with open(app.config["WORDLIST"]) as wl:
            return cls([line.strip() for line in wl.readlines()])
