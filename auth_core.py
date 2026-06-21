"""
auth_core.py - Authentication logic (no GUI). Shared by desktop and mobile apps.
"""

import hashlib
import secrets
import re
from database import get_connection


def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(32)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000,
    ).hex()
    return pwd_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    pwd_hash, _ = hash_password(password, salt)
    return pwd_hash == stored_hash


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_]{3,20}$", username))


def register_user(username: str, email: str, password: str) -> tuple:
    if not validate_username(username):
        return False, "Username must be 3-20 characters (letters, numbers, underscore)."
    if not validate_email(email):
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    pwd_hash, salt = hash_password(password)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (username, email, pwd_hash, salt),
            )
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
            from datetime import datetime as _dt
            now = _dt.now()
            cursor.execute(
                "INSERT INTO budgets (user_id, month, year, amount) VALUES (?, ?, ?, ?)",
                (user_id, now.month, now.year, 0.0),
            )
        return True, "Registration successful! You can now log in."
    except Exception as e:
        if "UNIQUE" in str(e):
            if "username" in str(e).lower():
                return False, "Username already exists."
            return False, "Email already registered."
        return False, f"Registration failed: {e}"


def login_user(username: str, password: str) -> tuple:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password_hash, salt FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if not row:
            return False, "Invalid username or password."
        if not verify_password(password, row["password_hash"], row["salt"]):
            return False, "Invalid username or password."
        return True, {"id": row["id"], "username": row["username"], "email": row["email"]}


def get_user_settings(user_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT theme, currency_symbol FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if row:
            return {"theme": row["theme"], "currency_symbol": row["currency_symbol"]}
    return {"theme": "dark", "currency_symbol": "₹"}


def update_user_settings(user_id: int, theme: str = None, currency_symbol: str = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if theme:
            cursor.execute(
                "UPDATE user_settings SET theme = ? WHERE user_id = ?",
                (theme, user_id),
            )
        if currency_symbol:
            cursor.execute(
                "UPDATE user_settings SET currency_symbol = ? WHERE user_id = ?",
                (currency_symbol, user_id),
            )
