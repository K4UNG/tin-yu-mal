from __future__ import annotations

from litestar import Controller, get, post
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_503_SERVICE_UNAVAILABLE

from app.ai import CourseGenerator
from app.course_schemas import (
    CourseOutline,
    ModuleContent,
    ModuleGenerateRequest,
    OutlineRequest,
    PrimaryLanguage,
    PromptSuggestionsResponse,
)


class CoursesController(Controller):
    path = "/courses"
    tags = ["Courses"]

    @get("/suggestions")
    async def suggestions(
        self,
        language: PrimaryLanguage = PrimaryLanguage.ENGLISH,
    ) -> PromptSuggestionsResponse:
        return PromptSuggestionsResponse(suggestions=CourseGenerator.suggestions(language=language))

    @post("/outline")
    async def outline(self, data: OutlineRequest, course_generator: CourseGenerator) -> CourseOutline:
        try:
            return await course_generator.generate_outline(data)
        except Exception as exc:
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Outline generation failed: {exc}",
            ) from exc

    @post("/modules/generate")
    async def generate_module(
        self,
        data: ModuleGenerateRequest,
        course_generator: CourseGenerator,
    ) -> ModuleContent:
        try:
            return await course_generator.generate_module(data)
        except Exception as exc:
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Module generation failed: {exc}",
            ) from exc
