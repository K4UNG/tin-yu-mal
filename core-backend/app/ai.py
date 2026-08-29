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
    CourseOutline,
    ModuleContent,
    ModuleGenerateRequest,
    OutlineRequest,
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
    """MVP course engine via Cursor SDK agents (text-only, JSON in / JSON out)."""

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
            tools=[],  # ponytail: no repo tools — we only need model text for course JSON
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
            # last resort: tolerate slightly messy JSON via loads → validate
            return schema.model_validate(json.loads(raw))

    async def generate_outline(self, request: OutlineRequest) -> CourseOutline:
        rules = LEVEL_RULES[request.level]
        module_count = int(rules["module_count"])
        lang = LANGUAGE_LABELS[request.language]
        schema_hint = json.dumps(CourseOutline.model_json_schema(), indent=2)

        prompt = f"""\
You are the course architect for tin-yu-mal, an AI learning app.
Generate a course OUTLINE only (no full lesson text).

Rules:
- Write all titles and summaries in {lang}.
- Produce exactly {module_count} chapters (index 1..{module_count}).
- Complexity level: {request.level.value}. {rules["guidance"]}
- Chapters must form a clear learning path: foundations → core idea → practice → synthesis.
- Keep summaries short (1-2 sentences). No markdown outside the JSON.

Return ONLY valid JSON matching this schema (no commentary):
{schema_hint}

Fill these fields exactly:
- topic: {request.topic.strip()!r}
- level: {request.level.value!r}
- language: {request.language.value!r}
"""
        outline = await self._prompt_model(prompt, CourseOutline)
        outline.topic = request.topic.strip()
        outline.level = request.level
        outline.language = request.language
        return outline

    async def generate_module(self, request: ModuleGenerateRequest) -> ModuleContent:
        rules = LEVEL_RULES[request.level]
        lang = LANGUAGE_LABELS[request.language]
        course_bit = f'Course title: "{request.course_title}". ' if request.course_title else ""
        schema_hint = json.dumps(ModuleContent.model_json_schema(), indent=2)

        prompt = f"""\
You are the lesson author for tin-yu-mal.
Generate ONE module as structured JSON for the frontend to render.

Rules:
- Write ALL text in {lang}.
- Complexity: {request.level.value}. {rules["guidance"]}
- Provide 2-5 teaching sections (plain paragraphs, no markdown headings).
- Include exactly ONE interactive block. Choose the best fit among:
  - quiz: short free-text answer + expected_answer + optional hint
  - multiple_choice: 3-4 options + correct_index (0-based)
  - flashcards: 3-8 front/back cards
- Do NOT invent other interactive types. Do NOT generate images or code UI.
- Match the chapter focus; do not cover the whole course.

Return ONLY valid JSON matching this schema (no commentary):
{schema_hint}

Context:
{course_bit}Topic: "{request.topic}". Chapter {request.chapter.index}: {request.chapter.title}.
Chapter goal: {request.chapter.summary}
Set level={request.level.value!r} and language={request.language.value!r}.
"""
        module = await self._prompt_model(prompt, ModuleContent)
        module.level = request.level
        module.language = request.language
        return module

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
