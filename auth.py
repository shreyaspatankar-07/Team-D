"""Local user authentication backed by SQLite."""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


DATABASE_FILE = Path(__file__).with_name("facility_auth.db")
HASH_ITERATIONS = 600_000


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    """Open, commit, and close a database connection."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialise_users() -> None:
    """Create the users table when the app is first started."""
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash BLOB NOT NULL,
                salt BLOB NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, HASH_ITERATIONS)


def register_user(name: str, username: str, password: str) -> tuple[bool, str]:
    """Create a user after validating the supplied credentials."""
    name = name.strip()
    username = username.strip()

    if not name:
        return False, "Enter your name."
    if len(name) > 100:
        return False, "Name must be 100 characters or fewer."
    if not username:
        return False, "Enter a username."
    if not 3 <= len(username) <= 50:
        return False, "Username must be between 3 and 50 characters."
    if not password:
        return False, "Enter a password."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    initialise_users()
    salt = os.urandom(16)
    password_hash = _password_hash(password, salt)
    try:
        with _connection() as connection:
            connection.execute(
                "INSERT INTO users (name, username, password_hash, salt) VALUES (?, ?, ?, ?)",
                (name, username, password_hash, salt),
            )
    except sqlite3.IntegrityError:
        return False, "That username is already registered."
    return True, "Registration successful. You can now log in."


def authenticate_user(username: str, password: str) -> tuple[bool, str, str | None]:
    """Validate credentials and return the matching display name."""
    if not username.strip() or not password:
        return False, "Enter both username and password.", None

    initialise_users()
    with _connection() as connection:
        user = connection.execute(
            "SELECT name, password_hash, salt FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()

    if user is None or not hmac.compare_digest(
        _password_hash(password, user["salt"]), user["password_hash"]
    ):
        return False, "Invalid username or password.", None
    return True, "Login successful.", user["name"]
