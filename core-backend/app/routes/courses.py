from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from litestar import Controller, Request, delete, get, post
from litestar.exceptions import ClientException, HTTPException, NotFoundException
from litestar.response import ServerSentEvent
from litestar.response.sse import ServerSentEventMessage
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_503_SERVICE_UNAVAILABLE
from pydantic import TypeAdapter
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.ai import CourseGenerator
from app.config import get_settings
from app.course_schemas import (
    ChapterEditRequest,
    ChapterRead,
    ChapterStatus as ChapterStatusSchema,
    ChapterSummary,
    ComplexityLevel as ComplexityLevelSchema,
    ContentBlock,
    CourseRead,
    CreateCourseRequest,
    EditHistoryEntry,
    PrimaryLanguage as PrimaryLanguageSchema,
    PromptSuggestionsResponse,
)
from app.db import session_scope
from app.extract import build_llm_context
from app.images import resolve_image_blocks
from app.models import Chapter, ChapterStatus, ComplexityLevel, Course, PrimaryLanguage, UploadedFile

log = logging.getLogger(__name__)

ContentBlockAdapter: TypeAdapter[Any] = TypeAdapter(ContentBlock)


def _chapters_if_loaded(course: Course) -> list[Chapter]:
    # Async session: never implicit-load relationships from sync code (MissingGreenlet).
    if "chapters" in sa_inspect(course).unloaded:
        return []
    return list(course.chapters)


def _to_course_read(course: Course) -> CourseRead:
    return CourseRead(
        id=course.id,
        topic=course.topic,
        level=ComplexityLevelSchema(course.level.value),
        language=PrimaryLanguageSchema(course.language.value),
        created_at=course.created_at,
        chapters=[
            ChapterSummary(
                id=ch.id,
                index=ch.index,
                title=ch.title,
                description=ch.description,
                status=ChapterStatusSchema(ch.status.value),
            )
            for ch in sorted(_chapters_if_loaded(course), key=lambda c: c.index)
        ],
    )


def _to_chapter_read(chapter: Chapter) -> ChapterRead:
    raw_blocks = chapter.blocks or []
    blocks = [ContentBlockAdapter.validate_python(b) for b in raw_blocks]
    history = [EditHistoryEntry.model_validate(h) for h in (chapter.edit_history or [])]
    return ChapterRead(id=chapter.id, title=chapter.title, blocks=blocks, edit_history=history)


async def _load_course(session: AsyncSession, course_id: UUID) -> Course:
    result = await session.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.chapters), selectinload(Course.files))
    )
    course = result.scalar_one_or_none()
    if course is None:
        raise NotFoundException(detail="Course not found")
    return course


async def _load_chapter(session: AsyncSession, course_id: UUID, chapter_id: UUID) -> tuple[Course, Chapter]:
    course = await _load_course(session, course_id)
    chapter = next((c for c in course.chapters if c.id == chapter_id), None)
    if chapter is None:
        raise NotFoundException(detail="Chapter not found")
    return course, chapter


def _source_context(course: Course) -> str:
    settings = get_settings()
    return build_llm_context(
        [(f.filename, f.extracted_text) for f in course.files],
        max_chars=settings.upload_context_max_chars,
    )


async def _fill_chapter_list(
    session_factory: async_sessionmaker[AsyncSession],
    course_generator: CourseGenerator,
    course_id: UUID,
    data: CreateCourseRequest,
    source_context: str,
) -> None:
    """Background outline fill. Empty `chapters` means still generating (or failed)."""
    try:
        generated = await course_generator.generate_chapter_list(
            data, source_context=source_context
        )
        async with session_scope(session_factory) as session:
            result = await session.execute(
                select(Course)
                .where(Course.id == course_id)
                .options(selectinload(Course.chapters))
            )
            course = result.scalar_one_or_none()
            if course is None or course.chapters:
                return
            course.chapters = [
                Chapter(
                    index=i,
                    title=item.title.strip(),
                    description=item.description.strip(),
                    status=ChapterStatus.NOT_GENERATED,
                    edit_history=[],
                )
                for i, item in enumerate(generated.chapters)
            ]
    except Exception:
        log.exception("Chapter list generation failed for course %s", course_id)


async def _generate_blocks(
    course: Course,
    chapter: Chapter,
    course_generator: CourseGenerator,
) -> list[ContentBlock]:
    surrounding = [c.title for c in sorted(course.chapters, key=lambda x: x.index) if c.id != chapter.id]
    generated = await course_generator.generate_chapter_content(
        topic=course.topic,
        level=ComplexityLevelSchema(course.level.value),
        language=PrimaryLanguageSchema(course.language.value),
        chapter_title=chapter.title,
        chapter_description=chapter.description,
        surrounding_titles=surrounding,
        source_context=_source_context(course),
    )
    return await resolve_image_blocks(generated.blocks)


class CoursesController(Controller):
    path = "/courses"
    tags = ["Courses"]

    @get("/suggestions")
    async def suggestions(
        self,
        language: PrimaryLanguageSchema = PrimaryLanguageSchema.ENGLISH,
    ) -> PromptSuggestionsResponse:
        return PromptSuggestionsResponse(suggestions=CourseGenerator.suggestions(language=language))

    @get("/")
    async def list_courses(self, db_session: AsyncSession) -> list[CourseRead]:
        result = await db_session.execute(
            select(Course)
            .options(selectinload(Course.chapters))
            .order_by(Course.created_at.desc())
        )
        return [_to_course_read(c) for c in result.scalars().all()]

    @post("/", status_code=HTTP_201_CREATED)
    async def create_course(
        self,
        data: CreateCourseRequest,
        db_session: AsyncSession,
        request: Request[Any, Any, Any],
    ) -> CourseRead:
        settings = get_settings()
        source_context = ""
        upload_rows: list[UploadedFile] = []
        if data.file_ids:
            result = await db_session.execute(
                select(UploadedFile).where(UploadedFile.id.in_(data.file_ids))
            )
            upload_rows = list(result.scalars().all())
            found = {row.id for row in upload_rows}
            missing = [str(fid) for fid in data.file_ids if fid not in found]
            if missing:
                raise NotFoundException(detail=f"Unknown file_ids: {', '.join(missing)}")
            source_context = build_llm_context(
                [(row.filename, row.extracted_text) for row in upload_rows],
                max_chars=settings.upload_context_max_chars,
            )

        course = Course(
            topic=data.topic.strip(),
            level=ComplexityLevel(data.level.value),
            language=PrimaryLanguage(data.language.value),
            chapters=[],
        )
        db_session.add(course)
        await db_session.flush()
        for row in upload_rows:
            row.course_id = course.id
        read = _to_course_read(course)
        await db_session.commit()

        # ponytail: in-process task so POST can return an id to poll. SAQ if the API process shouldn't own LLM work.
        asyncio.create_task(
            _fill_chapter_list(
                request.app.state["session_factory"],
                request.app.state["course_generator"],
                course.id,
                data,
                source_context,
            )
        )
        return read

    @get("/{course_id:uuid}")
    async def get_course(self, course_id: UUID, db_session: AsyncSession) -> CourseRead:
        return _to_course_read(await _load_course(db_session, course_id))

    @delete("/{course_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_course(self, course_id: UUID, db_session: AsyncSession) -> None:
        course = await _load_course(db_session, course_id)
        for row in list(course.files):
            await db_session.delete(row)
        await db_session.delete(course)

    @get("/{course_id:uuid}/chapters/{chapter_id:uuid}")
    async def get_chapter(
        self,
        course_id: UUID,
        chapter_id: UUID,
        db_session: AsyncSession,
    ) -> ChapterRead:
        _, chapter = await _load_chapter(db_session, course_id, chapter_id)
        if chapter.status != ChapterStatus.READY or not chapter.blocks:
            raise ClientException(detail="Chapter content is not ready yet")
        return _to_chapter_read(chapter)

    @post("/{course_id:uuid}/chapters/{chapter_id:uuid}/generate")
    async def generate_chapter(
        self,
        course_id: UUID,
        chapter_id: UUID,
        db_session: AsyncSession,
        course_generator: CourseGenerator,
        stream: bool = False,
    ) -> Any:
        course, chapter = await _load_chapter(db_session, course_id, chapter_id)
        if chapter.status == ChapterStatus.GENERATING:
            raise ClientException(detail="Chapter is already generating")

        chapter.status = ChapterStatus.GENERATING
        await db_session.flush()

        if stream:
            return ServerSentEvent(_stream_generate(db_session, course, chapter, course_generator))

        try:
            blocks = await _generate_blocks(course, chapter, course_generator)
        except Exception as exc:
            chapter.status = ChapterStatus.NOT_GENERATED
            await db_session.flush()
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Chapter generation failed: {exc}",
            ) from exc

        chapter.blocks = [b.model_dump(mode="json") for b in blocks]
        chapter.status = ChapterStatus.READY
        await db_session.flush()
        return _to_chapter_read(chapter)

    @post("/{course_id:uuid}/chapters/{chapter_id:uuid}/edit")
    async def edit_chapter(
        self,
        course_id: UUID,
        chapter_id: UUID,
        data: ChapterEditRequest,
        db_session: AsyncSession,
        course_generator: CourseGenerator,
    ) -> ChapterRead:
        course, chapter = await _load_chapter(db_session, course_id, chapter_id)
        if chapter.status != ChapterStatus.READY or not chapter.blocks:
            raise ClientException(detail="Generate the chapter before editing")

        existing = [ContentBlockAdapter.validate_python(b) for b in chapter.blocks]
        try:
            revised = await course_generator.edit_chapter_content(
                blocks=existing,
                edit=data,
                language=PrimaryLanguageSchema(course.language.value),
            )
            blocks = await resolve_image_blocks(revised.blocks)
        except Exception as exc:
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Chapter edit failed: {exc}",
            ) from exc

        history = list(chapter.edit_history or [])
        history.append({"prompt": data.prompt.strip(), "timestamp": datetime.now(UTC).isoformat()})
        chapter.blocks = [b.model_dump(mode="json") for b in blocks]
        chapter.edit_history = history
        await db_session.flush()
        return _to_chapter_read(chapter)


async def _stream_generate(
    db_session: AsyncSession,
    course: Course,
    chapter: Chapter,
    course_generator: CourseGenerator,
) -> AsyncGenerator[ServerSentEventMessage, None]:
    """SSE: status → each block → complete. Cursor returns full JSON; we stream blocks after."""
    yield ServerSentEventMessage(event="status", data=json.dumps({"status": "generating"}))
    try:
        blocks = await _generate_blocks(course, chapter, course_generator)
        for i, block in enumerate(blocks):
            yield ServerSentEventMessage(
                event="block",
                data=json.dumps({"index": i, "block": block.model_dump(mode="json")}),
            )
        chapter.blocks = [b.model_dump(mode="json") for b in blocks]
        chapter.status = ChapterStatus.READY
        await db_session.flush()
        yield ServerSentEventMessage(
            event="complete",
            data=json.dumps(_to_chapter_read(chapter).model_dump(mode="json")),
        )
    except Exception as exc:
        chapter.status = ChapterStatus.NOT_GENERATED
        await db_session.flush()
        yield ServerSentEventMessage(event="error", data=json.dumps({"detail": str(exc)}))
