"""API / LLM contracts aligned with SPECS.md."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ComplexityLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PrimaryLanguage(StrEnum):
    ENGLISH = "en"
    BURMESE = "my"


class ChapterStatus(StrEnum):
    NOT_GENERATED = "not_generated"
    GENERATING = "generating"
    READY = "ready"


# Depth knobs — chapter count scales with level (SPECS §5.1).
LEVEL_RULES: dict[ComplexityLevel, dict[str, str | int]] = {
    ComplexityLevel.BEGINNER: {
        "module_count": 7,
        "guidance": (
            "More, shorter chapters that build slowly. Simple language, lots of analogies, "
            "define every term. Prefer guided interactives (quiz_mc, flashcards)."
        ),
    },
    ComplexityLevel.INTERMEDIATE: {
        "module_count": 5,
        "guidance": (
            "Balanced depth. Some prior knowledge OK. Mix guided and open-ended interactives."
        ),
    },
    ComplexityLevel.ADVANCED: {
        "module_count": 4,
        "guidance": (
            "Fewer, denser chapters. Assume prior knowledge, less hand-holding. "
            "Favor open-ended quiz_free interactives."
        ),
    },
}


# --- Request / response (SPECS §3.1–3.2, §7) ---


class CreateCourseRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    level: ComplexityLevel = ComplexityLevel.BEGINNER
    language: PrimaryLanguage = PrimaryLanguage.ENGLISH
    file_ids: list[UUID] = Field(
        default_factory=list,
        description="Optional uploaded file IDs to ground chapter generation",
    )


class UploadedFileRead(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    has_text: bool
    created_at: datetime


class ChapterSummary(BaseModel):
    id: UUID
    index: int = Field(ge=0)
    title: str
    description: str
    status: ChapterStatus


class CourseRead(BaseModel):
    id: UUID
    topic: str
    level: ComplexityLevel
    language: PrimaryLanguage
    chapters: list[ChapterSummary]
    created_at: datetime


# --- LLM-only shapes (server assigns id / status / index) ---


class GeneratedChapter(BaseModel):
    title: str
    description: str = Field(description="1-sentence chapter description")


class GeneratedChapterList(BaseModel):
    chapters: list[GeneratedChapter] = Field(min_length=4, max_length=7)


# --- Full chapter content (schemas ready; endpoints later) ---


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    markdown: str


class ImageBlock(BaseModel):
    type: Literal["image"] = "image"
    prompt: str
    alt: str
    url: str = ""


class QuizFreeBlock(BaseModel):
    type: Literal["quiz_free"] = "quiz_free"
    question: str
    sample_answer: str
    grading_rubric: str


class QuizMcBlock(BaseModel):
    type: Literal["quiz_mc"] = "quiz_mc"
    question: str
    options: list[str] = Field(min_length=3, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str


class FlashcardItem(BaseModel):
    front: str
    back: str


class FlashcardsBlock(BaseModel):
    type: Literal["flashcards"] = "flashcards"
    cards: list[FlashcardItem] = Field(min_length=2, max_length=12)


ContentBlock = Annotated[
    TextBlock | ImageBlock | QuizFreeBlock | QuizMcBlock | FlashcardsBlock,
    Field(discriminator="type"),
]


class EditHistoryEntry(BaseModel):
    prompt: str
    timestamp: datetime


class ChapterRead(BaseModel):
    id: UUID
    title: str
    blocks: list[ContentBlock]
    edit_history: list[EditHistoryEntry] = Field(default_factory=list)


class GeneratedChapterContent(BaseModel):
    """LLM output for chapter body — server resolves image URLs after."""

    blocks: list[ContentBlock] = Field(min_length=3, max_length=24)


class ChapterEditRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


class QuizEvaluateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    sample_answer: str = Field(min_length=1, max_length=4000)
    grading_rubric: str = Field(min_length=1, max_length=4000)
    user_answer: str = Field(min_length=1, max_length=8000)


class QuizEvaluateResponse(BaseModel):
    verdict: Literal["correct", "partial", "incorrect"]
    feedback: str


class PromptSuggestion(BaseModel):
    label: str
    topic: str


class PromptSuggestionsResponse(BaseModel):
    suggestions: list[PromptSuggestion]
