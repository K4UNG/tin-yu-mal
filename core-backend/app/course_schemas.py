"""Course generation contracts for the tin-yu-mal MVP.

MVP loop: topic + level + language → outline → pick chapter → module (text + 1 interactive).
Interactive types are a fixed set — frontend renders them; LLM only fills JSON.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ComplexityLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PrimaryLanguage(StrEnum):
    ENGLISH = "en"
    BURMESE = "my"


# Depth knobs — not just tone. Used in prompts so level is a product decision.
LEVEL_RULES: dict[ComplexityLevel, dict[str, str | int]] = {
    ComplexityLevel.BEGINNER: {
        "module_count": 6,
        "guidance": (
            "More modules that build slowly. Simple language, lots of analogies, "
            "define every term. Interactives must be guided (clear hints, one correct path)."
        ),
    },
    ComplexityLevel.INTERMEDIATE: {
        "module_count": 5,
        "guidance": (
            "Balanced depth. Some prior knowledge OK. Interactives can require light reasoning "
            "but still have a clear answer."
        ),
    },
    ComplexityLevel.ADVANCED: {
        "module_count": 4,
        "guidance": (
            "Fewer, denser modules. Assume prior knowledge, less hand-holding. "
            "Interactives can be more open-ended (harder quiz prompts, fewer hints)."
        ),
    },
}


class ChapterOutline(BaseModel):
    index: int = Field(ge=1, description="1-based chapter order")
    title: str
    summary: str = Field(description="1-2 sentence description of what this chapter covers")


class CourseOutline(BaseModel):
    title: str
    level: ComplexityLevel
    language: PrimaryLanguage
    topic: str
    chapters: list[ChapterOutline] = Field(min_length=4, max_length=6)


class OutlineRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500, description="What the user wants to learn")
    level: ComplexityLevel = ComplexityLevel.BEGINNER
    language: PrimaryLanguage = PrimaryLanguage.ENGLISH


class QuizInteractive(BaseModel):
    type: Literal["quiz"] = "quiz"
    instruction: str
    expected_answer: str = Field(description="Canonical short answer for checking")
    hint: str | None = None


class MultipleChoiceInteractive(BaseModel):
    type: Literal["multiple_choice"] = "multiple_choice"
    instruction: str
    options: list[str] = Field(min_length=3, max_length=4)
    correct_index: int = Field(ge=0, le=3)


class FlashcardItem(BaseModel):
    front: str
    back: str


class FlashcardsInteractive(BaseModel):
    type: Literal["flashcards"] = "flashcards"
    cards: list[FlashcardItem] = Field(min_length=3, max_length=8)


InteractiveBlock = Annotated[
    QuizInteractive | MultipleChoiceInteractive | FlashcardsInteractive,
    Field(discriminator="type"),
]


class ModuleContent(BaseModel):
    title: str
    level: ComplexityLevel
    language: PrimaryLanguage
    # Ordered teaching paragraphs (frontend stacks them; image slots are future work)
    sections: list[str] = Field(min_length=2, max_length=6)
    interactive: InteractiveBlock


class ModuleGenerateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    level: ComplexityLevel
    language: PrimaryLanguage
    chapter: ChapterOutline
    course_title: str | None = None


class PromptSuggestion(BaseModel):
    label: str
    topic: str


class PromptSuggestionsResponse(BaseModel):
    suggestions: list[PromptSuggestion]
