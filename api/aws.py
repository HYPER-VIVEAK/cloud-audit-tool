"""AWS client helpers."""

import boto3

from .config import settings


def aws_client(
    service: str,
    access_key_id: str | None = None,
    secret_key: str | None = None,
    region: str | None = None,
):
    session = boto3.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_key,
        region_name=region or settings.aws_region,
    )
    return session.client(service)
