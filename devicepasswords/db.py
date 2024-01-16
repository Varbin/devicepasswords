from datetime import datetime
from typing import List

from flask import current_app, Flask
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    """Table of users."""
    __tablename__ = "users"

    primary: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    tokens: Mapped[List["Token"]] = relationship()


class Token(db.Model):
    __tablename__ = "tokens"

    primary: Mapped[int] = mapped_column(Integer, primary_key=True)
    user: Mapped[str] = mapped_column(ForeignKey("users.primary"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    expires: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class Log(db.Model):
    __tablename__ = "logs"

    primary: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    token: Mapped[int] = mapped_column(ForeignKey("tokens.primary"))


class Session(db.Model):
    __tablename__ = "session"

    sid: Mapped[str] = mapped_column(String, primary_key=True)
    sub: Mapped[str] = mapped_column(String, nullable=False)
    id_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, nullable=True)
    refresh_token_expiration: Mapped[datetime] = mapped_column(DateTime,
                                                               nullable=True)

def init_db(app: Flask):
    db.init_app(app)
    with app.app_context():
        db.create_all()
