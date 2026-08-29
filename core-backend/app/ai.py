from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TypeVar

from cursor_sdk import (
    AgentOptions,
    AsyncAgent,
    AsyncClient,
    LocalAgentOptions,
    ModelParameterValue,
    ModelSelection,
)
from pydantic import BaseModel, TypeAdapter, ValidationError

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

log = logging.getLogger(__name__)

DEMO_SUGGESTIONS = [
    PromptSuggestion(label="How neural networks work", topic="How neural networks work"),
    PromptSuggestion(label="How a car engine works", topic="How a four-stroke car engine works"),
    PromptSuggestion(label="Photosynthesis", topic="How photosynthesis works in plants"),
    PromptSuggestion(label="How the internet works", topic="How the internet routes a packet from A to B"),
]

T = TypeVar("T", bound=BaseModel)
_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_JSON_RETRY = (
    "Your previous reply was empty or not valid JSON. "
    "Reply with ONLY the JSON object from the original schema. "
    "No markdown fences, no commentary, no tool calls."
)
_IX_RETRY = (
    "The previous JSON is missing required interactive blocks. Return the FULL chapter JSON again, "
    "keeping the text/image blocks, and include at least one of EACH: quiz_mc, quiz_free, and flashcards "
    "as separate objects in blocks. Never write these as markdown in a text block."
)
_CONTENT_SCHEMA = """
{"blocks":[ /* ordered ContentBlock objects */ ]}
text:       {"type":"text","markdown":"## Heading\\n\\nParagraph. GFM tables are fine."}
image:      {"type":"image","prompt":"what to show","alt":"alt text","url":""}
quiz_mc:    {"type":"quiz_mc","question":"...","options":["A","B","C","D"],"correct_index":0,"explanation":"..."}
quiz_free:  {"type":"quiz_free","question":"...","sample_answer":"...","grading_rubric":"..."}
flashcards: {"type":"flashcards","cards":[{"front":"...","back":"..."}]}
Quizzes MUST be quiz_mc / quiz_free / flashcards objects — never markdown in a text block.
Every chapter MUST include at least one of each of those three types.
"""
_INTERACTIVE = frozenset({"quiz_mc", "quiz_free", "flashcards"})
_TYPE_ALIAS = {
    "quiz": "quiz_mc",
    "mc": "quiz_mc",
    "mcq": "quiz_mc",
    "multiple_choice": "quiz_mc",
    "multiplechoice": "quiz_mc",
    "quiz_multiple_choice": "quiz_mc",
    "free": "quiz_free",
    "freeform": "quiz_free",
    "free_response": "quiz_free",
    "short_answer": "quiz_free",
    "open_ended": "quiz_free",
    "flashcard": "flashcards",
    "flash_card": "flashcards",
    "flash_cards": "flashcards",
}
_BlockAdapter: TypeAdapter[ContentBlock] = TypeAdapter(ContentBlock)


def _extract_json(text: str) -> str:
    text = (text or "").strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    obj, arr = text.find("{"), text.find("[")
    if obj == -1 and arr == -1:
        return text
    if arr == -1 or (obj != -1 and obj < arr):
        start, end = obj, text.rfind("}")
    else:
        start, end = arr, text.rfind("]")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _loads_json(blob: str) -> object | None:
    if not blob or not blob.strip():
        return None
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        try:
            data, _ = json.JSONDecoder().raw_decode(blob)
            return data
        except json.JSONDecodeError:
            return None


def _alias_block(raw: object) -> object:
    if not isinstance(raw, dict):
        return raw
    t = str(raw.get("type", "")).strip().lower().replace("-", "_").replace(" ", "_")
    t = _TYPE_ALIAS.get(t, t)
    out = dict(raw)
    out["type"] = t
    if t == "quiz_mc":
        if "options" not in out:
            for key in ("choices", "answers", "items"):
                if key in out:
                    out["options"] = out[key]
                    break
        if "correct_index" not in out:
            for key in ("correct", "answer", "correctIndex", "answer_index"):
                if key in out:
                    out["correct_index"] = out[key]
                    break
        ci, opts = out.get("correct_index"), out.get("options")
        if isinstance(ci, str) and isinstance(opts, list):
            if ci.isdigit():
                out["correct_index"] = int(ci)
            elif len(ci) == 1 and ci.isalpha():
                out["correct_index"] = ord(ci.lower()) - 97
            elif ci in opts:
                out["correct_index"] = opts.index(ci)
        if "explanation" not in out:
            out["explanation"] = out.get("explain") or out.get("rationale") or ""
    if t == "flashcards" and "cards" not in out:
        out["cards"] = out.get("items") or out.get("flashcards") or []
    return out


def _coerce_blocks(data: object) -> object:
    if isinstance(data, list):
        data = {"blocks": data}
    if not isinstance(data, dict) or not isinstance(data.get("blocks"), list):
        return data
    kept = []
    for raw in data["blocks"]:
        try:
            kept.append(_BlockAdapter.validate_python(_alias_block(raw)).model_dump(mode="json"))
        except ValidationError:
            continue
    return {**data, "blocks": kept}


def _ix_types(content: GeneratedChapterContent) -> set[str]:
    return {b.type for b in content.blocks if b.type in _INTERACTIVE}


def _has_ix(content: GeneratedChapterContent) -> bool:
    return _INTERACTIVE <= _ix_types(content)


def _parse_schema(text: str, schema: type[T]) -> T | None:
    data = _loads_json(_extract_json(text))
    if data is None:
        return None
    if "blocks" in schema.model_fields:
        data = _coerce_blocks(data)
    elif isinstance(data, list) and "chapters" in schema.model_fields:
        data = {"chapters": data}
    try:
        return schema.model_validate(data)
    except ValidationError:
        return None


assert _extract_json("") == ""
assert _extract_json('Sure.\n{"blocks": []}') == '{"blocks": []}'
assert _extract_json("```json\n[1]\n```") == "[1]"
assert _extract_json('[{ "title": "A" }]') == '[{ "title": "A" }]'
assert _loads_json("") is None
assert _loads_json("{") is None
_alias_sample = _parse_schema(
    json.dumps(
        {
            "blocks": [
                {"type": "text", "markdown": "a"},
                {"type": "text", "markdown": "b"},
                {"type": "text", "markdown": "c"},
                {
                    "type": "quiz",
                    "question": "Q?",
                    "choices": ["x", "y", "z"],
                    "correct": 0,
                    "explanation": "e",
                },
            ]
        }
    ),
    GeneratedChapterContent,
)
assert _alias_sample is not None and any(b.type == "quiz_mc" for b in _alias_sample.blocks)
assert not _has_ix(_alias_sample)
_ix_sample = _parse_schema(
    json.dumps(
        {
            "blocks": [
                {"type": "text", "markdown": "a"},
                {
                    "type": "quiz_mc",
                    "question": "Q?",
                    "options": ["x", "y", "z"],
                    "correct_index": 0,
                    "explanation": "e",
                },
                {
                    "type": "quiz_free",
                    "question": "Q2?",
                    "sample_answer": "a",
                    "grading_rubric": "must mention a",
                },
                {
                    "type": "flashcards",
                    "cards": [{"front": "f1", "back": "b1"}, {"front": "f2", "back": "b2"}],
                },
            ]
        }
    ),
    GeneratedChapterContent,
)
assert _ix_sample is not None and _has_ix(_ix_sample)


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
        # ponytail: composer-2.5 has no thinking=false; fast=true is the no-extended-reasoning variant.
        return AgentOptions(
            api_key=api_key.get_secret_value(),
            model=ModelSelection(
                id=self.settings.cursor_model,
                params=[ModelParameterValue(id="fast", value="true")],
            ),
            tools=tools,
            local=LocalAgentOptions(cwd=self.settings.cursor_workspace),
        )

    async def _run_text(self, agent: AsyncAgent, prompt: str) -> str:
        run = await agent.send(prompt)
        chunks: list[str] = []
        async for piece in run.iter_text():
            chunks.append(piece)
        result = await run.wait()
        log.info(
            "cursor run id=%s status=%s duration_ms=%s chars=%s",
            result.id,
            result.status,
            result.duration_ms,
            len(result.result or "") or sum(len(c) for c in chunks),
        )
        if result.status == "error":
            raise RuntimeError(f"Cursor agent run failed (id={result.id})")
        # ponytail: result.result is empty after some tool-only / thinking turns; stream text is the fallback
        return (result.result or "").strip() or "".join(chunks).strip()

    async def _prompt_model(
        self,
        prompt: str,
        schema: type[T],
        *,
        with_web: bool = False,
        require_ix: bool = False,
    ) -> T:
        options = self._agent_options(with_web=with_web)
        log.info("cursor prompt with_web=%s tools=%s", with_web, list(options.tools or []))
        prompt = (
            prompt
            + "\n\nYour final message MUST be the JSON object only "
            "(tool use first is fine; do not end on commentary or an empty message)."
        )
        agent = await AsyncAgent.create(options, client=self.client)
        try:
            text = await self._run_text(agent, prompt)
            parsed = _parse_schema(text, schema)
            if parsed is None:
                log.warning("cursor JSON missing or invalid; retrying once")
                text = await self._run_text(agent, _JSON_RETRY)
                parsed = _parse_schema(text, schema)
            if parsed is None:
                raise RuntimeError("Model returned empty or invalid JSON")
            if require_ix and isinstance(parsed, GeneratedChapterContent) and not _has_ix(parsed):
                missing = ", ".join(sorted(_INTERACTIVE - _ix_types(parsed)))
                log.warning("cursor chapter missing interactives (%s); retrying once", missing)
                text = await self._run_text(
                    agent,
                    f"{_IX_RETRY} Missing types: {missing}.",
                )
                again = _parse_schema(text, schema)
                if again is not None:
                    parsed = again
            if require_ix and isinstance(parsed, GeneratedChapterContent) and not _has_ix(parsed):
                missing = ", ".join(sorted(_INTERACTIVE - _ix_types(parsed)))
                raise RuntimeError(f"Chapter is missing required interactives: {missing}")
            return parsed
        finally:
            await agent.close()

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
- text.markdown MUST be markdown (headings, bold, lists, GFM tables, code where useful).
- Include typically 1-3 image blocks where a visual helps. For image blocks set prompt+alt; leave url as "".
- blocks MUST include at least one of EACH interactive type as its own object:
  quiz_mc (multiple-choice), quiz_free (typed answer), and flashcards.
  Typical placement: quiz_mc mid-chapter, flashcards after a concept, quiz_free near the end.
  Do NOT write questions as markdown — they will not render as quizzes.
- Cover ONLY this chapter — do not teach the whole course.
- Surrounding chapters for continuity: {neighbors}

After researching, return ONLY valid JSON matching this schema (no commentary):
{_CONTENT_SCHEMA}

Course topic: {topic!r}
Chapter title: {chapter_title!r}
Chapter description: {chapter_description!r}
{context_block}
"""
        return await self._prompt_model(
            prompt, GeneratedChapterContent, with_web=True, require_ix=True
        )

    async def edit_chapter_content(
        self,
        *,
        blocks: list[ContentBlock],
        edit: ChapterEditRequest,
        language: PrimaryLanguage,
    ) -> GeneratedChapterContent:
        lang = LANGUAGE_LABELS[language]
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
Keep at least one quiz_mc, one quiz_free, and one flashcards unless the user explicitly asks to remove them.
For any new image blocks, leave url as "".

After any research, return ONLY valid JSON matching this schema (no commentary):
{_CONTENT_SCHEMA}
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
