# SPDX-License-Identifier: MPL-2.0
"""
Device password generation.
"""
import math
import random

from flask import Flask

wordlist = []


class DevicePasswords:
    """Device password generator from list."""
    def __init__(self, words: list[str], digits=5, entropy=64):
        self.secure = random.SystemRandom()
        self.words = words

        self.digits = digits
        self.wordcount = int(math.ceil(
            (entropy - math.log2(10) * digits) / math.log2(len(words))
        ))

    def generate(self) -> str:
        """Generate device password consisting of words and numbers, joined by
        dashes."""
        suffix = "".join(
            str(self.secure.randint(0, 9)) for _ in range(self.digits)
        )

        return "-".join(
            self.secure.choice(self.words).strip() for _ in range(
                self.wordcount
            )
        ) + "-" + suffix

    @classmethod
    def from_app(cls, app: Flask):
        """Creates DevicePasswords instance from a Flask application where
        the config parameter WORDLIST is set to a line separated list of words.
        """
        with open(app.config["WORDLIST"]) as wl:
            return cls([line.strip() for line in wl.readlines()],
                       entropy=app.config["PASSWORD_ENTROPY"])
