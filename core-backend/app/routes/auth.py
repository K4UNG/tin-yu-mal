from __future__ import annotations

from typing import Any

from litestar import Controller, Request, get, post
from litestar.exceptions import NotAuthorizedException
from litestar.status_codes import HTTP_200_OK
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import jwt_auth
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserRead
from app.security import verify_password


class AuthController(Controller):
    path = "/auth"
    tags = ["Auth"]

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
