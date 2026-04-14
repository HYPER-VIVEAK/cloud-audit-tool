"""MySQL-backed storage for user cloud credentials."""

from typing import Any

from .crypto import decrypt_value, encrypt_value
from .db import mysql_connection


def list_credentials(user_id: int, platform: str | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT id, user_id, platform, environment, region, access_key_id, created_at, last_used
        FROM credentials
        WHERE user_id = %s
    """
    params: list[Any] = [user_id]
    if platform:
        query += " AND platform = %s"
        params.append(platform)
    query += " ORDER BY created_at DESC, id DESC"

    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "platform": row["platform"],
            "environment": row["environment"],
            "region": row.get("region"),
            "access_key_id": row["access_key_id"],
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "last_used": row["last_used"].isoformat() if row.get("last_used") else None,
        }
        for row in rows
    ]


def create_credential(
    user_id: int,
    platform: str,
    environment: str,
    region: str | None,
    access_key_id: str,
    secret_key: str,
) -> dict[str, Any]:
    encrypted_secret = encrypt_value(secret_key)
    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO credentials (
                    user_id, platform, environment, region, access_key_id, secret_key_encrypted
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, platform, environment, region, access_key_id, encrypted_secret),
            )
            credential_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT id, user_id, platform, environment, region, access_key_id, created_at, last_used
                FROM credentials
                WHERE id = %s
                LIMIT 1
                """,
                (credential_id,),
            )
            row = cursor.fetchone()

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "platform": row["platform"],
        "environment": row["environment"],
        "region": row.get("region"),
        "access_key_id": row["access_key_id"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "last_used": row["last_used"].isoformat() if row.get("last_used") else None,
    }


def get_credential_for_user(user_id: int, credential_id: int) -> dict[str, Any] | None:
    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, platform, environment, region, access_key_id, secret_key_encrypted
                FROM credentials
                WHERE id = %s AND user_id = %s
                LIMIT 1
                """,
                (credential_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute(
                """
                UPDATE credentials
                SET last_used = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (credential_id,),
            )

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "platform": row["platform"],
        "environment": row["environment"],
        "region": row.get("region"),
        "access_key_id": row["access_key_id"],
        "secret_key": decrypt_value(row["secret_key_encrypted"]),
    }
