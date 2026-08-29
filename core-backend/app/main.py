from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
import asyncio

from cursor_sdk import AsyncClient
from litestar import Litestar, Request
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar_saq import QueueConfig, SAQConfig, SAQPlugin
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import CourseGenerator
from app.auth import jwt_auth
from app.config import Settings, get_settings
from app.db import Base, create_engine, create_session_factory
from app.models import Chapter, Course, UploadedFile, User  # noqa: F401 — register metadata
from app.routes import api_router
from app.security import hash_password
from app.storage import ensure_bucket
from app.tasks import sample_task


async def provide_db_session(request: Request[Any, Any, Any]) -> AsyncGenerator[AsyncSession, None]:
    session_factory = request.app.state["session_factory"]
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def provide_course_generator(request: Request[Any, Any, Any]) -> CourseGenerator:
    return request.app.state["course_generator"]


async def bootstrap_admin(session: AsyncSession, settings: Settings) -> None:
    result = await session.execute(select(User).where(User.email == settings.bootstrap_email.lower()))
    if result.scalar_one_or_none() is not None:
        return
    session.add(
        User(
            email=settings.bootstrap_email.lower(),
            name=settings.bootstrap_name,
            password_hash=hash_password(settings.bootstrap_password.get_secret_value()),
        )
    )
    await session.commit()


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    app.state["engine"] = engine
    app.state["session_factory"] = session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        await bootstrap_admin(session, settings)

    await asyncio.to_thread(ensure_bucket, settings)

    # Cursor local bridge stays open for the app lifetime (required for AsyncAgent).
    async with await AsyncClient.launch_bridge(workspace=settings.cursor_workspace) as client:
        app.state["cursor_client"] = client
        app.state["course_generator"] = CourseGenerator(settings=settings, client=client)
        yield

    await engine.dispose()


def create_saq_plugin(settings: Settings) -> SAQPlugin:
    return SAQPlugin(
        config=SAQConfig(
            use_server_lifespan=False,
            queue_configs=[
                QueueConfig(
                    name="default",
                    dsn=settings.redis_url,
                    tasks=[sample_task],
                )
            ],
        )
    )


def create_app() -> Litestar:
    settings = get_settings()
    return Litestar(
        route_handlers=[api_router],
        lifespan=[lifespan],
        plugins=[create_saq_plugin(settings)],
        dependencies={
            "db_session": Provide(provide_db_session),
            "course_generator": Provide(provide_course_generator, sync_to_thread=False),
        },
        cors_config=CORSConfig(
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        openapi_config=OpenAPIConfig(
            title=settings.app_name,
            version="0.1.0",
            render_plugins=[ScalarRenderPlugin()],
        ),
        on_app_init=[jwt_auth.on_app_init],
        debug=settings.debug,
    )


app = create_app()
