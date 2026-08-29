from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypeVar

from cursor_sdk import AgentOptions, AsyncAgent, AsyncClient, LocalAgentOptions
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.course_schemas import (
    LEVEL_RULES,
    CreateCourseRequest,
    GeneratedChapterList,
    PrimaryLanguage,
    PromptSuggestion,
)

LANGUAGE_LABELS = {
    PrimaryLanguage.ENGLISH: "English",
    PrimaryLanguage.BURMESE: "Burmese (မြန်မာ)",
}

DEMO_SUGGESTIONS = [
    PromptSuggestion(label="How neural networks work", topic="How neural networks work"),
    PromptSuggestion(label="How a car engine works", topic="How a four-stroke car engine works"),
    PromptSuggestion(label="Photosynthesis", topic="How photosynthesis works in plants"),
    PromptSuggestion(label="How the internet works", topic="How the internet routes a packet from A to B"),
]

T = TypeVar("T", bound=BaseModel)
_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _extract_json_object(text: str) -> str:
    text = text.strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        return fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


class CourseGenerator:
    """Cursor SDK course generation. Chapter-list first (SPECS §5.1)."""

    def __init__(self, settings: Settings, client: AsyncClient) -> None:
        self.settings = settings
        self.client = client
        Path(settings.cursor_workspace).mkdir(parents=True, exist_ok=True)

    def _agent_options(self) -> AgentOptions:
        api_key = self.settings.cursor_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise RuntimeError("CURSOR_API_KEY is not set")
        return AgentOptions(
            api_key=api_key.get_secret_value(),
            model=self.settings.cursor_model,
            tools=[],
            local=LocalAgentOptions(cwd=self.settings.cursor_workspace),
        )

    async def _prompt_model(self, prompt: str, schema: type[T]) -> T:
        result = await AsyncAgent.prompt(prompt, self._agent_options(), client=self.client)
        if result.status == "error":
            raise RuntimeError(f"Cursor agent run failed (id={result.id})")
        raw = _extract_json_object(result.result or "")
        try:
            return schema.model_validate_json(raw)
        except ValidationError:
            return schema.model_validate(json.loads(raw))

    async def generate_chapter_list(self, request: CreateCourseRequest) -> GeneratedChapterList:
        rules = LEVEL_RULES[request.level]
        chapter_count = int(rules["module_count"])
        lang = LANGUAGE_LABELS[request.language]
        schema_hint = json.dumps(GeneratedChapterList.model_json_schema(), indent=2)

        prompt = f"""\
You are the course architect for tin-yu-mal, an AI learning app.
Generate a CHAPTER LIST only (titles + one-sentence descriptions). No full lesson content.

Rules:
- Write all titles and descriptions in {lang}.
- Produce exactly {chapter_count} chapters.
- Complexity level: {request.level.value}. {rules["guidance"]}
- Chapters must form a clear learning path: foundations → core idea → practice → synthesis.
- Each description is exactly one sentence.
- Do not include ids, indexes, or status fields — only title and description.

Return ONLY valid JSON matching this schema (no commentary):
{schema_hint}

Topic: {request.topic.strip()!r}
"""
        return await self._prompt_model(prompt, GeneratedChapterList)

    @staticmethod
    def suggestions(*, language: PrimaryLanguage = PrimaryLanguage.ENGLISH) -> list[PromptSuggestion]:
        if language == PrimaryLanguage.BURMESE:
            return [
                PromptSuggestion(label="Neural network ဆိုတာ", topic="Neural network ဘယ်လိုအလုပ်လုပ်လဲ"),
                PromptSuggestion(label="ကားအင်ဂျင်", topic="ကားအင်ဂျင် ဘယ်လိုအလုပ်လုပ်လဲ"),
                PromptSuggestion(label="Photosynthesis", topic="အပင်များ photosynthesis ဘယ်လိုလုပ်သလဲ"),
                PromptSuggestion(label="Internet", topic="Internet က packet တစ်ခုကို ဘယ်လိုပို့လဲ"),
            ]
        return list(DEMO_SUGGESTIONS)
