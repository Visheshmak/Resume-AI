from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


async def register_user(db: AsyncSession, request: RegisterRequest) -> User:
    email = str(request.email).lower()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(email=email, full_name=request.full_name.strip(), password_hash=hash_password(request.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, request: LoginRequest) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == str(request.email).lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token, jti, expires_at = create_access_token(user.id)
    db.add(UserSession(user_id=user.id, token_jti=jti, expires_at=expires_at))
    await db.commit()
    return TokenResponse(access_token=token, expires_in=int((expires_at - datetime.now(UTC)).total_seconds()))
