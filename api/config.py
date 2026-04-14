"""Configuration helpers for the API layer."""

import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """Settings loaded from environment variables."""

    app_name: str = os.getenv("APP_NAME", "Cloud Audit API")
    api_prefix: str = os.getenv("API_PREFIX", "/api")

    # Auth
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "session_token")
    session_cookie_secure: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    session_ttl: timedelta = timedelta(days=int(os.getenv("SESSION_DAYS", "7")))
    credentials_secret: str = os.getenv("CREDENTIALS_SECRET", "change-this-credentials-secret")

    # CORS
    cors_allow_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    # AWS
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")

    # MySQL
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_database: str = os.getenv("MYSQL_DATABASE", "cloud_audit_db")
    mysql_user: str = os.getenv("MYSQL_USER", "mysqladmin")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "mysqlpassword")

    # MongoDB
    mongo_host: str = os.getenv("MONGO_HOST", "localhost")
    mongo_port: int = int(os.getenv("MONGO_PORT", "27017"))
    mongo_database: str = os.getenv("MONGO_INITDB_DATABASE", "mongoappdb")
    mongo_user: str = os.getenv("MONGO_INITDB_ROOT_USERNAME", "mongoadmin")
    mongo_password: str = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "mongopassword")
    mongo_collection: str = os.getenv("MONGO_SCAN_COLLECTION", "scan_results")

    # Scan metadata
    scan_platform: str = os.getenv("SCAN_PLATFORM", "AWS")
    scan_environment: str = os.getenv("SCAN_ENVIRONMENT", "Prod")


settings = Settings()
