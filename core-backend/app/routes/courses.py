from __future__ import annotations

from uuid import UUID

from litestar import Controller, get, post
from litestar.exceptions import HTTPException, NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_503_SERVICE_UNAVAILABLE
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai import CourseGenerator
from app.course_schemas import (
    ChapterStatus as ChapterStatusSchema,
    ChapterSummary,
    ComplexityLevel as ComplexityLevelSchema,
    CourseRead,
    CreateCourseRequest,
    PrimaryLanguage as PrimaryLanguageSchema,
    PromptSuggestionsResponse,
)
from app.extract import build_llm_context
from app.config import get_settings
from app.models import Chapter, ChapterStatus, ComplexityLevel, Course, PrimaryLanguage, UploadedFile


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
            for ch in course.chapters
        ],
    )


class CoursesController(Controller):
    path = "/courses"
    tags = ["Courses"]

    @get("/suggestions")
    async def suggestions(
        self,
        language: PrimaryLanguageSchema = PrimaryLanguageSchema.ENGLISH,
    ) -> PromptSuggestionsResponse:
        return PromptSuggestionsResponse(suggestions=CourseGenerator.suggestions(language=language))

    @post("/", status_code=HTTP_201_CREATED)
    async def create_course(
        self,
        data: CreateCourseRequest,
        db_session: AsyncSession,
        course_generator: CourseGenerator,
    ) -> CourseRead:
        """Generate chapter list and persist course (SPECS §7 POST /courses)."""
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

        try:
            generated = await course_generator.generate_chapter_list(
                data,
                source_context=source_context,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Chapter list generation failed: {exc}",
            ) from exc

        course = Course(
            topic=data.topic.strip(),
            level=ComplexityLevel(data.level.value),
            language=PrimaryLanguage(data.language.value),
            chapters=[
                Chapter(
                    index=i,
                    title=item.title.strip(),
                    description=item.description.strip(),
                    status=ChapterStatus.NOT_GENERATED,
                    edit_history=[],
                )
                for i, item in enumerate(generated.chapters)
            ],
        )
        db_session.add(course)
        await db_session.flush()
        for row in upload_rows:
            row.course_id = course.id
        loaded = await db_session.execute(
            select(Course).where(Course.id == course.id).options(selectinload(Course.chapters))
        )
        return _to_course_read(loaded.scalar_one())

    @get("/{course_id:uuid}")
    async def get_course(self, course_id: UUID, db_session: AsyncSession) -> CourseRead:
        result = await db_session.execute(
            select(Course).where(Course.id == course_id).options(selectinload(Course.chapters))
        )
        course = result.scalar_one_or_none()
        if course is None:
            raise NotFoundException(detail="Course not found")
        course.chapters.sort(key=lambda c: c.index)
        return _to_course_read(course)
