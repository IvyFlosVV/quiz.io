"""User registration, login, and password hashing with SHA-256 and random salt."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from typing import Any

USERS_FILE = "users.json"


def _hash_password(password: str, salt: bytes) -> str:
    """Return hex digest of SHA-256(password + salt)."""
    return hashlib.sha256(salt + password.encode("utf-8")).hexdigest()


def hash_password(password: str) -> tuple[str, str]:
    """
    Hash a password with a new random salt.

    Returns:
        (password_hash_hex, salt_hex)
    """
    salt = secrets.token_bytes(16)
    digest = _hash_password(password, salt)
    return digest, salt.hex()


def verify_password(password: str, salt_hex: str, password_hash_hex: str) -> bool:
    """Verify password against stored salt and hash."""
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    return secrets.compare_digest(_hash_password(password, salt), password_hash_hex)


def load_users() -> dict[str, Any]:
    """Load users from disk, or return empty dict if missing."""
    if not os.path.isfile(USERS_FILE):
        return {}
    with open(USERS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_users(users: dict[str, Any]) -> None:
    """Persist users to JSON."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def username_valid(username: str) -> bool:
    """Non-empty alphanumeric username."""
    return bool(username) and bool(re.fullmatch(r"[A-Za-z0-9]+", username))


def register_interactive(getpass_fn) -> str:
    """
    Prompt for new username and password; save hashed credentials.

    Returns:
        The new username.
    """
    users = load_users()
    while True:
        username = input("Choose a username (letters and numbers only): ").strip()
        if not username_valid(username):
            print("Username must be non-empty and alphanumeric only.")
            continue
        if username in users:
            print("That username is already taken. Try another.")
            continue
        break

    while True:
        password = getpass_fn("Choose a password (at least 6 characters): ")
        if len(password) < 6:
            print("Password must be at least 6 characters.")
            continue
        confirm = getpass_fn("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Try again.")
            continue
        break

    pwd_hash, salt_hex = hash_password(password)
    users[username] = {"salt": salt_hex, "password_hash": pwd_hash}
    save_users(users)
    print("Account created! Let's get started.")
    return username


def login_interactive(getpass_fn, max_attempts: int = 3) -> str | None:
    """
    Prompt for username and password up to max_attempts times.

    Returns:
        Username on success, or None if all attempts failed.
    """
    users = load_users()
    attempts = 0
    while attempts < max_attempts:
        username = input("Username: ").strip()
        password = getpass_fn("Password: ")
        if username not in users:
            print("Invalid username or password.")
            attempts += 1
            continue
        entry = users[username]
        if verify_password(password, entry["salt"], entry["password_hash"]):
            return username
        print("Invalid username or password.")
        attempts += 1
    return None
