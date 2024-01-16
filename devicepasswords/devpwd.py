import random

from flask import current_app, Flask

wordlist = []


class DevicePasswords:
    def __init__(self, words: list[str, ...]):
        self.secure = random.SystemRandom()
        self.words = words

    def generate(self) -> str:
        suffix = str(self.secure.randint(0, 99999)).rjust(5, '0')

        return "-".join(
            self.secure.choice(self.words).strip() for _ in range(4)
        ) + "-" + suffix

    @classmethod
    def from_app(cls, app: Flask):
        with open(app.config["WORDLIST"]) as wl:
            return cls([line.strip() for line in wl.readlines()])
