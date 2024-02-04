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
    secure = random.SystemRandom()
    wordcount: int

    def __init__(self, words: list[str] = None, digits=5, entropy=64):
        self.words = words or []

        self.digits = digits
        self.entropy = entropy
        if words:
            self.calculate_wordcount()

    def calculate_wordcount(self):
        """Calculate the required words."""
        self.wordcount = int(math.ceil(
            (self.entropy - math.log2(10) * self.digits) /
             math.log2(len(self.words))
        ))

    def generate(self) -> str:
        """Generate device password consisting of words and numbers, joined by
        dashes."""
        return "-".join(
            self.secure.choice(self.words).strip() for _ in range(
                self.wordcount
            )
        ) + "-" + self.random_digits(self.digits)

    def init_app(self, app: Flask) -> None:
        with open(app.config["WORDLIST"]) as wl:
            self.words = [line.strip() for line in wl.readlines()]

        self.entropy = app.config["PASSWORD_ENTROPY"]
        self.calculate_wordcount()

    @classmethod
    def random_digits(cls, amount: int) -> str:
        """Generates 'amount' random digits."""
        return "".join(
            str(cls.secure.randint(0, 9)) for _ in range(amount)
        )


device_passwords = DevicePasswords()
