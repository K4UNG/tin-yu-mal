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
    ChapterEditRequest,
    ComplexityLevel,
    ContentBlock,
    CreateCourseRequest,
    GeneratedChapterContent,
    GeneratedChapterList,
    PrimaryLanguage,
    PromptSuggestion,
    QuizEvaluateRequest,
    QuizEvaluateResponse,
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
    """Cursor SDK course generation (chapter list + chapter body + quiz grading)."""

    def __init__(self, settings: Settings, client: AsyncClient) -> None:
        self.settings = settings
        self.client = client
        Path(settings.cursor_workspace).mkdir(parents=True, exist_ok=True)

    def _agent_options(self, *, with_web: bool = False) -> AgentOptions:
        api_key = self.settings.cursor_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise RuntimeError("CURSOR_API_KEY is not set")
        # ponytail: webSearch/webFetch only — no shell/edit so the agent can't mutate the host
        tools = ["webSearch", "webFetch"] if with_web and self.settings.cursor_web_tools else []
        return AgentOptions(
            api_key=api_key.get_secret_value(),
            model=self.settings.cursor_model,
            tools=tools,
            local=LocalAgentOptions(cwd=self.settings.cursor_workspace),
        )

    async def _prompt_model(self, prompt: str, schema: type[T], *, with_web: bool = False) -> T:
        result = await AsyncAgent.prompt(
            prompt,
            self._agent_options(with_web=with_web),
            client=self.client,
        )
        if result.status == "error":
            raise RuntimeError(f"Cursor agent run failed (id={result.id})")
        raw = _extract_json_object(result.result or "")
        try:
            return schema.model_validate_json(raw)
        except ValidationError:
            return schema.model_validate(json.loads(raw))

    async def generate_chapter_list(
        self,
        request: CreateCourseRequest,
        *,
        source_context: str = "",
    ) -> GeneratedChapterList:
        rules = LEVEL_RULES[request.level]
        chapter_count = int(rules["module_count"])
        lang = LANGUAGE_LABELS[request.language]
        schema_hint = json.dumps(GeneratedChapterList.model_json_schema(), indent=2)

        context_block = ""
        if source_context.strip():
            context_block = f"""
User-provided source material (use to ground chapter topics; do not copy verbatim):
---
{source_context.strip()}
---
"""

        prompt = f"""\
You are the course architect for tin-yu-mal, an AI learning app.
Generate a CHAPTER LIST only (titles + one-sentence descriptions). No full lesson content.

Research first:
- Use webSearch (and webFetch on the best sources) to gather current, accurate information about the topic
  before deciding chapter structure. Prefer reputable sources.

Rules:
- Write all titles and descriptions in {lang}.
- Produce exactly {chapter_count} chapters.
- Complexity level: {request.level.value}. {rules["guidance"]}
- Chapters must form a clear learning path: foundations → core idea → practice → synthesis.
- Each description is exactly one sentence.
- Do not include ids, indexes, or status fields — only title and description.
- If source material is provided, align chapters with that material where relevant.

After researching, return ONLY valid JSON matching this schema (no commentary):
{schema_hint}

Topic: {request.topic.strip()!r}
{context_block}
"""
        return await self._prompt_model(prompt, GeneratedChapterList, with_web=True)

    async def generate_chapter_content(
        self,
        *,
        topic: str,
        level: ComplexityLevel,
        language: PrimaryLanguage,
        chapter_title: str,
        chapter_description: str,
        surrounding_titles: list[str],
        source_context: str = "",
    ) -> GeneratedChapterContent:
        rules = LEVEL_RULES[level]
        lang = LANGUAGE_LABELS[language]
        schema_hint = json.dumps(GeneratedChapterContent.model_json_schema(), indent=2)
        neighbors = ", ".join(surrounding_titles) if surrounding_titles else "(none)"

        context_block = ""
        if source_context.strip():
            context_block = f"""
Source material (ground facts when relevant; do not dump verbatim):
---
{source_context.strip()}
---
"""

        prompt = f"""\
You are the lesson author for tin-yu-mal.
Generate ONE chapter as an ordered array of content blocks for the frontend to render.

Research first:
- Use webSearch and webFetch to pull up-to-date facts, examples, and explanations for this chapter
  before writing content. Ground the lesson in what you find; do not invent outdated claims.

Rules:
- Write ALL learner-facing text in {lang}. JSON keys stay in English.
- Complexity: {level.value}. {rules["guidance"]}
- text.markdown MUST be markdown (headings, bold, lists, code where useful).
- Include typically 1-3 image blocks where a visual helps. For image blocks set prompt+alt; leave url as "".
- Include at least 2 interactive blocks total from: quiz_mc, quiz_free, flashcards.
  Beginner: prefer quiz_mc + flashcards. Advanced: prefer quiz_free.
- Cover ONLY this chapter — do not teach the whole course.
- Surrounding chapters for continuity: {neighbors}

After researching, return ONLY valid JSON matching this schema (no commentary):
{schema_hint}

Course topic: {topic!r}
Chapter title: {chapter_title!r}
Chapter description: {chapter_description!r}
{context_block}
"""
        return await self._prompt_model(prompt, GeneratedChapterContent, with_web=True)

    async def edit_chapter_content(
        self,
        *,
        blocks: list[ContentBlock],
        edit: ChapterEditRequest,
        language: PrimaryLanguage,
    ) -> GeneratedChapterContent:
        lang = LANGUAGE_LABELS[language]
        schema_hint = json.dumps(GeneratedChapterContent.model_json_schema(), indent=2)
        current = json.dumps(
            [b.model_dump(mode="json") for b in blocks],
            ensure_ascii=False,
            indent=2,
        )

        prompt = f"""\
You are editing an existing tin-yu-mal chapter.
Here is the current chapter content:
{current}

The user requests this change: {edit.prompt.strip()!r}

If the edit needs fresher facts or examples, use webSearch / webFetch first.
Return the FULL revised content in the same JSON schema, applying only the requested change
and leaving everything else consistent. Keep learner-facing text in {lang}.
For any new image blocks, leave url as "".

After any research, return ONLY valid JSON matching this schema (no commentary):
{schema_hint}
"""
        return await self._prompt_model(prompt, GeneratedChapterContent, with_web=True)

    async def evaluate_quiz(self, data: QuizEvaluateRequest) -> QuizEvaluateResponse:
        schema_hint = json.dumps(QuizEvaluateResponse.model_json_schema(), indent=2)
        prompt = f"""\
You are a strict but fair quiz grader for tin-yu-mal.

Question: {data.question}
Sample answer (reference, not shown to learner): {data.sample_answer}
Grading rubric: {data.grading_rubric}
Learner answer: {data.user_answer}

Return ONLY JSON matching this schema:
{schema_hint}

verdict must be exactly one of: correct, partial, incorrect.
feedback should be short, helpful, and in the same language as the question.
"""
        return await self._prompt_model(prompt, QuizEvaluateResponse)

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
