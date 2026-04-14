"""Minimal MySQL helpers for auth-backed user lookup."""

import pymysql
from contextlib import contextmanager

from pymysql.cursors import DictCursor

from .config import settings


ADMIN_SEED_HASH = "$2b$12$KzS.bRGW66C5WiBdO8EEpeJ3itdp5Gp3zpB6jHmYwdcHYPfvQrszK"


@contextmanager
def mysql_connection():
    connection = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        cursorclass=DictCursor,
        autocommit=True,
    )
    try:
        yield connection
    finally:
        connection.close()


def ensure_auth_schema() -> None:
    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS credentials (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    platform VARCHAR(20) NOT NULL,
                    environment VARCHAR(20) NOT NULL,
                    region VARCHAR(50) NULL,
                    access_key_id VARCHAR(255) NOT NULL,
                    secret_key_encrypted TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            try:
                cursor.execute("ALTER TABLE credentials ADD COLUMN region VARCHAR(50) NULL AFTER environment")
            except pymysql.err.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE credentials ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER secret_key_encrypted")
            except pymysql.err.OperationalError:
                pass
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token_hash CHAR(64) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE username = username
                """,
                ("admin", ADMIN_SEED_HASH, "admin"),
            )
