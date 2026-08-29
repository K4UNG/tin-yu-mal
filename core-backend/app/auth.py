from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID

from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTAuth, Token
from sqlalchemy import select

from app.config import get_settings
from app.models import User


async def retrieve_user_handler(
    token: Token,
    connection: ASGIConnection[Any, Any, Any, Any],
) -> User | None:
    session_factory = connection.app.state["session_factory"]
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.id == UUID(token.sub)))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            return None
        # detach so the request can use the user after the session closes
        session.expunge(user)
        return user


def create_jwt_auth() -> JWTAuth[User]:
    settings = get_settings()
    return JWTAuth[User](
        retrieve_user_handler=retrieve_user_handler,
        token_secret=settings.secret_key.get_secret_value(),
        default_token_expiration=timedelta(seconds=settings.jwt_expiration_seconds),
        exclude=["/health", "/auth/login", "/auth/signup", "/schema", "/courses", "/uploads"],
    )


jwt_auth = create_jwt_auth()
