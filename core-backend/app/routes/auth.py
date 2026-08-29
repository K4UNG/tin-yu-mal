from __future__ import annotations

from typing import Any

from litestar import Controller, Request, get, post
from litestar.exceptions import ClientException, NotAuthorizedException
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import jwt_auth
from app.models import User
from app.schemas import LoginRequest, SignupRequest, TokenResponse, UserRead
from app.security import hash_password, verify_password


class AuthController(Controller):
    path = "/auth"
    tags = ["Auth"]

    @post("/signup", status_code=HTTP_201_CREATED)
    async def signup(self, data: SignupRequest, db_session: AsyncSession) -> TokenResponse:
        email = data.email.lower()
        existing = await db_session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            raise ClientException(detail="Email already registered", status_code=HTTP_409_CONFLICT)

        user = User(email=email, name=data.name, password_hash=hash_password(data.password))
        db_session.add(user)
        try:
            await db_session.flush()
        except IntegrityError as exc:
            raise ClientException(
                detail="Email already registered", status_code=HTTP_409_CONFLICT
            ) from exc

        return TokenResponse(access_token=jwt_auth.create_token(identifier=str(user.id)))

    @post("/login", status_code=HTTP_200_OK)
    async def login(self, data: LoginRequest, db_session: AsyncSession) -> TokenResponse:
        result = await db_session.execute(select(User).where(User.email == data.email.lower()))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active or not verify_password(data.password, user.password_hash):
            raise NotAuthorizedException(detail="Invalid email or password")

        return TokenResponse(access_token=jwt_auth.create_token(identifier=str(user.id)))

    @get("/me")
    async def me(self, request: Request[User, Any, Any]) -> UserRead:
        return UserRead.model_validate(request.user)
