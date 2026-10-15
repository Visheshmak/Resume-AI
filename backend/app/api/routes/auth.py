from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import bearer_scheme, get_current_user, get_db
from app.core.security import decode_access_token
from app.models import User, UserSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.common import MessageResponse
from app.services.auth import authenticate_user, register_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register a user")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    return await register_user(db, request)


@router.post("/login", response_model=TokenResponse, summary="Create an authenticated session")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await authenticate_user(db, request)


@router.post("/logout", response_model=MessageResponse, summary="Revoke the current session")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    payload = decode_access_token(credentials.credentials)
    await db.execute(
        update(UserSession).where(UserSession.user_id == user.id, UserSession.token_jti == str(payload["jti"])).values(revoked_at=datetime.now(UTC))
    )
    await db.commit()
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse, summary="Get the current user")
async def me(user: User = Depends(get_current_user)) -> User:
    return user
