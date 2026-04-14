"""Authentication routes."""

import pymysql
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from . import auth
from .users import authenticate_user, create_user, get_user_by_username, list_users


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    message: str
    username: str
    role: str
    scope: list[str]


class MeResponse(BaseModel):
    username: str
    role: str
    scope: list[str]


class UserSummaryResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: str | None
    scope: list[str]


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, response: Response):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    auth.prune_expired_sessions()
    session_token = auth.create_session(user["id"])
    auth.set_session_cookie(response, session_token)

    return LoginResponse(
        message="Login successful",
        username=user["username"],
        role=user["role"],
        scope=user["scope"],
    )

@router.post("/logout")
async def logout(request: Request, response: Response):
    auth.delete_session(request.cookies.get(auth.settings.session_cookie_name))
    auth.clear_session_cookie(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=MeResponse)
async def me(current_user=Depends(auth.get_current_user)):
    user = get_user_by_username(current_user.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return MeResponse(username=user["username"], role=user["role"], scope=current_user.scope)


@router.get("/users", response_model=list[UserSummaryResponse])
async def get_users(_: auth.SessionUser = Depends(auth.require_scopes(["users:manage"]))):
    return [UserSummaryResponse(**user) for user in list_users()]


@router.post("/users", response_model=UserSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_user_account(
    payload: CreateUserRequest,
    _: auth.SessionUser = Depends(auth.require_scopes(["users:manage"])),
):
    if payload.role not in {"admin", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if len(payload.username.strip()) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username too short")
    if len(payload.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password too short")

    try:
        user = create_user(payload.username.strip(), payload.password, payload.role)
    except pymysql.err.IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists") from exc

    return UserSummaryResponse(**user)
