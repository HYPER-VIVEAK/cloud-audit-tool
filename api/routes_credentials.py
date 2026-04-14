"""Credential management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .auth import SessionUser, require_scopes
from .credentials_store import create_credential, list_credentials


router = APIRouter(prefix="/credentials", tags=["credentials"])


class CredentialCreateRequest(BaseModel):
    platform: str
    environment: str
    region: str | None = None
    access_key_id: str
    secret_key: str


class CredentialResponse(BaseModel):
    id: int
    user_id: int
    platform: str
    environment: str
    region: str | None
    access_key_id: str
    created_at: str | None
    last_used: str | None


@router.get("", response_model=list[CredentialResponse])
async def get_credentials(current_user: SessionUser = Depends(require_scopes(["scan:run"]))):
    return [CredentialResponse(**row) for row in list_credentials(current_user.user_id)]


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def add_credential(
    payload: CredentialCreateRequest,
    current_user: SessionUser = Depends(require_scopes(["scan:run"])),
):
    platform = payload.platform.upper()
    if platform not in {"AWS", "AZURE", "GCP"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform")
    if len(payload.environment.strip()) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Environment too short")
    if len(payload.access_key_id.strip()) < 4 or len(payload.secret_key.strip()) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credential values look invalid")

    row = create_credential(
        user_id=current_user.user_id,
        platform=platform,
        environment=payload.environment.strip(),
        region=payload.region.strip() if payload.region else None,
        access_key_id=payload.access_key_id.strip(),
        secret_key=payload.secret_key.strip(),
    )
    return CredentialResponse(**row)
