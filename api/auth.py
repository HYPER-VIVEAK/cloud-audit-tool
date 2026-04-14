"""Session-based authentication helpers for FastAPI routes."""

from datetime import datetime, timezone
import hashlib
import secrets
from typing import Iterable

from fastapi import Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel

from .config import settings
from .db import mysql_connection


class SessionUser(BaseModel):
    user_id: int
    username: str
    role: str
    scope: list[str]


ROLE_SCOPES = {
    "admin": ["scan:run", "iam:read", "s3:read", "ec2:read", "users:manage"],
    "user": ["scan:run", "iam:read", "s3:read", "ec2:read"],
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=int(settings.session_ttl.total_seconds()),
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = _utc_now() + settings.session_ttl

    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sessions (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token_hash, expires_at),
            )

    return token


def delete_session(token: str | None) -> None:
    if not token:
        return

    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM sessions
                WHERE token_hash = %s
                """,
                (_hash_token(token),),
            )


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> SessionUser:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session")

    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id, u.username, u.role, s.expires_at
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s
                LIMIT 1
                """,
                (_hash_token(session_token),),
            )
            row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    expires_at = row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= _utc_now():
        delete_session(session_token)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    return SessionUser(
        user_id=row["id"],
        username=row["username"],
        role=row["role"],
        scope=ROLE_SCOPES.get(row["role"], ROLE_SCOPES["user"]),
    )


def require_scopes(required: Iterable[str]):
    required_set = set(required)

    def dependency(user: SessionUser = Depends(get_current_user)) -> SessionUser:
        if not required_set.issubset(set(user.scope)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return user

    return dependency


def prune_expired_sessions() -> None:
    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM sessions
                WHERE expires_at <= %s
                """,
                (_utc_now(),),
            )
