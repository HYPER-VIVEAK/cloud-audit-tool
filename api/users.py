"""User access helpers for MySQL-backed authentication."""

from typing import Any

import bcrypt

from .auth import ROLE_SCOPES
from .db import mysql_connection


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, password_hash, role
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username,),
            )
            user = cursor.fetchone()

    if not user:
        return None

    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "scope": ROLE_SCOPES.get(user["role"], ROLE_SCOPES["user"]),
    }


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, role
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username,),
            )
            user = cursor.fetchone()

    if not user:
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "scope": ROLE_SCOPES.get(user["role"], ROLE_SCOPES["user"]),
    }


def list_users() -> list[dict[str, Any]]:
    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, role, created_at
                FROM users
                ORDER BY created_at DESC, id DESC
                """
            )
            users = cursor.fetchall()

    return [
        {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "created_at": user["created_at"].isoformat() if user["created_at"] else None,
            "scope": ROLE_SCOPES.get(user["role"], ROLE_SCOPES["user"]),
        }
        for user in users
    ]


def create_user(username: str, password: str, role: str = "user") -> dict[str, Any]:
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                """,
                (username, password_hash, role),
            )
            user_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT id, username, role, created_at
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            user = cursor.fetchone()

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"].isoformat() if user["created_at"] else None,
        "scope": ROLE_SCOPES.get(user["role"], ROLE_SCOPES["user"]),
    }
