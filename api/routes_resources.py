"""Resource inspection endpoints for IAM, S3, and EC2."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from .auth import SessionUser, require_scopes
from .aws import aws_client
from .credentials_store import get_credential_for_user
from .mongo_store import fetch_scan_metadata

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resources", tags=["resources"])


def _resolve_aws_client(current_user: SessionUser, service_name: str, scan_id: str | None):
    if not scan_id:
        return aws_client(service_name)

    metadata = fetch_scan_metadata(current_user.user_id, scan_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Selected scan not found")

    credential_id = metadata.get("credential_id")
    if not isinstance(credential_id, int):
        raise HTTPException(
            status_code=400,
            detail="Selected scan does not include credential metadata. Run a new scan and try again.",
        )

    credential = get_credential_for_user(current_user.user_id, credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential for selected scan no longer exists")
    if credential.get("platform") != "AWS":
        raise HTTPException(status_code=400, detail="Selected scan platform is not supported for resource listing")

    return aws_client(
        service_name,
        credential["access_key_id"],
        credential["secret_key"],
        credential.get("region"),
    )


@router.get("/iam/users")
async def list_iam_users(
    scan_id: str | None = Query(default=None),
    current_user: SessionUser = Depends(require_scopes(["iam:read"])),
):
    try:
        client = _resolve_aws_client(current_user, "iam", scan_id)
        paginator = client.get_paginator("list_users")
        users = []
        for page in paginator.paginate():
            for user in page.get("Users", []):
                users.append({
                    "user_name": user.get("UserName"),
                    "arn": user.get("Arn"),
                    "created": user.get("CreateDate"),
                })
        return {"users": users}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("IAM list users failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list IAM users") from exc


@router.get("/s3/buckets")
async def list_buckets(
    scan_id: str | None = Query(default=None),
    current_user: SessionUser = Depends(require_scopes(["s3:read"])),
):
    try:
        client = _resolve_aws_client(current_user, "s3", scan_id)
        resp = client.list_buckets()
        buckets = [
            {"name": b.get("Name"), "created": b.get("CreationDate")}
            for b in resp.get("Buckets", [])
        ]
        return {"buckets": buckets}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("S3 list buckets failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list buckets") from exc


@router.get("/ec2/instances")
async def list_instances(
    scan_id: str | None = Query(default=None),
    current_user: SessionUser = Depends(require_scopes(["ec2:read"])),
):
    try:
        client = _resolve_aws_client(current_user, "ec2", scan_id)
        paginator = client.get_paginator("describe_instances")
        instances: List[dict] = []
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    instances.append({
                        "instance_id": inst.get("InstanceId"),
                        "type": inst.get("InstanceType"),
                        "state": inst.get("State", {}).get("Name"),
                        "public_ip": inst.get("PublicIpAddress"),
                        "private_ip": inst.get("PrivateIpAddress"),
                        "tags": inst.get("Tags", []),
                    })
        return {"instances": instances}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("EC2 list instances failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list instances") from exc
