from __future__ import annotations

from litestar import Controller, post
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_503_SERVICE_UNAVAILABLE

from app.ai import CourseGenerator
from app.course_schemas import QuizEvaluateRequest, QuizEvaluateResponse


class QuizController(Controller):
    path = "/quiz"
    tags = ["Quiz"]

    @post("/evaluate")
    async def evaluate(
        self,
        data: QuizEvaluateRequest,
        course_generator: CourseGenerator,
    ) -> QuizEvaluateResponse:
        try:
            return await course_generator.evaluate_quiz(data)
        except Exception as exc:
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Quiz evaluation failed: {exc}",
            ) from exc
