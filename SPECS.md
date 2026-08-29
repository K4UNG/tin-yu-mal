# AI Course Generator — Hackathon MVP Specs

## 1. Overview

An AI app that generates full interactive courses on any topic a user requests. The user picks a topic, a complexity level, and a primary language. The AI generates a chapter list, and each chapter is generated on-demand with markdown content, inline images, and interactive components (quiz, multiple-choice, flashcards). After a chapter is generated, the user can request edits to it via a free-text prompt.

**Stack:** Litestar (Python) backend, SvelteKit frontend.

**Scope discipline:** everything below is MVP unless marked `[stretch]`. If time runs short, cut stretch items first, then cut interaction types down to just multiple-choice.

---

## 2. Core User Flow

1. **Home screen** — user enters:
  - Topic (free text, e.g. "How neural networks work")
  - Complexity level: `Beginner` / `Intermediate` / `Advanced`
  - Primary language: `English` / `Burmese`
2. **Chapter generation** — LLM generates a **Chapters** list (renamed from "outline"): 4-7 chapters, each with a title + 1-sentence description. Rendered as a clickable list.
3. **Chapter entry** — user clicks a chapter → LLM generates full chapter content (markdown text + inline images + interactive components), streamed in.
4. **Post-generation edit** — once a chapter finishes generating, an edit prompt box appears. User types a modification request (e.g. "make this simpler," "add an example about cars," "remove the second image"). LLM regenerates the chapter (or patches it) based on the prompt + existing content.
5. User navigates between chapters freely once generated.

---

## 3. Data Models

### 3.1 Course

```json
{
  "id": "uuid",
  "topic": "string",
  "level": "beginner | intermediate | advanced",
  "language": "en | my",
  "chapters": [ChapterSummary],
  "created_at": "iso8601"
}
```

### 3.2 ChapterSummary (from chapter-list generation step)

```json
{
  "id": "uuid",
  "index": 0,
  "title": "string",
  "description": "string (1 sentence)",
  "status": "not_generated | generating | ready"
}
```

### 3.3 Chapter (full content, generated on entry)

```json
{
  "id": "uuid",
  "title": "string",
  "blocks": [ContentBlock],
  "edit_history": [ { "prompt": "string", "timestamp": "iso8601" } ]
}
```

### 3.4 ContentBlock (ordered array — this is the chapter body)

Each block is one of the following types. The LLM outputs an ordered array of these; the frontend renders each block with the matching Svelte component.

`**text` block**

```json
{ "type": "text", "markdown": "string (markdown content)" }
```

`**image` block**

```json
{
  "type": "image",
  "prompt": "string (what the image should depict)",
  "alt": "string",
  "url": "string (filled in after image resolution step)"
}
```

`**quiz_free` block** (free-answer, LLM-evaluated)

```json
{
  "type": "quiz_free",
  "question": "string",
  "sample_answer": "string (for LLM grading reference, not shown to user)",
  "grading_rubric": "string (short, what a correct answer needs to include)"
}
```

`**quiz_mc` block** (multiple-choice)

```json
{
  "type": "quiz_mc",
  "question": "string",
  "options": ["string", "string", "string", "string"],
  "correct_index": 0,
  "explanation": "string (shown after answering)"
}
```

`**flashcards` block**

```json
{
  "type": "flashcards",
  "cards": [{ "front": "string", "back": "string" }]
}
```

---

## 4. Interaction Types — Detail

### 4.1 Multiple-choice quiz

- Render options as buttons. On click: highlight correct/incorrect, show `explanation`.
- No backend call needed at answer-time — grading is static (`correct_index`).

### 4.2 Free-answer quiz (LLM-evaluated)

- User types an answer, submits.
- Frontend sends `{question, sample_answer, grading_rubric, user_answer}` to a backend evaluation endpoint.
- Backend calls LLM with a strict grading prompt → returns `{ verdict: "correct" | "partial" | "incorrect", feedback: "string" }`.
- Render verdict + feedback below the answer box.
- **Note:** this is the one interaction requiring a live LLM call after chapter generation — budget for latency (show a loading state).

### 4.3 Flashcards

- Simple flip-card carousel. Front shown by default, click/tap flips to back. Next/prev navigation.
- No backend interaction needed after generation.

---

## 5. Chapter Generation Prompting

### 5.1 Chapter-list generation

Input: `topic`, `level`, `language`.
Output: JSON array of `ChapterSummary` (title + description only, no `id`/`status` — assign those server-side).

- Number of chapters should scale with `level`: Beginner → more, shorter chapters (e.g. 6-7); Advanced → fewer, denser chapters (e.g. 4-5).

### 5.2 Chapter content generation

Input: `topic`, `level`, `language`, chapter `title` + `description`, surrounding chapter titles (for context/continuity).
Output: JSON array of `ContentBlock`.

- All `text` block content **must be markdown** (headings, bold, lists, code blocks where relevant).
- All narrative text must be in the selected `language` (English or Burmese). Interaction JSON keys stay in English; question/answer/option *content* is in the selected language.
- Effort/depth scales with `level`:
  - Beginner: more `text` blocks, simpler language, more analogies, more guided interactions (favor `quiz_mc`, `flashcards`).
  - Advanced: denser `text`, assumes prior knowledge, more open-ended interactions (favor `quiz_free`).
- The LLM decides where to insert `image` blocks and how many (typically 1-3 per chapter) based on where a visual would aid understanding — don't hardcode positions.
- Mix of interaction blocks: aim for at least 2 interaction blocks per chapter (e.g. one `quiz_mc` mid-chapter, one `flashcards` or `quiz_free` near the end).

### 5.3 Chapter edit (post-generation)

Input: existing `Chapter.blocks`, user's edit `prompt`.
Output: revised `blocks` array (full replacement is simplest for MVP — don't attempt diff/patch logic under time pressure).

- Append `{prompt, timestamp}` to `edit_history`.
- Prompt template: "Here is the current chapter content: [blocks JSON]. The user requests this change: [prompt]. Return the full revised content in the same JSON schema, applying only the requested change and leaving everything else consistent."

---

## 6. Image Resolution

The LLM only outputs an `image` block's `prompt` + `alt` — it does not produce the actual image. Pick **one** approach based on time remaining:

- **Fast/safe (recommended for MVP):** use a stock photo search API (e.g. Unsplash API) with the `prompt` as the search query. Fast, no cost, no generation latency, "good enough" for most demo topics.
- **Stretch `[stretch]`:** call an actual image-generation API for a fully custom image per block. Higher wow-factor but adds latency + cost + failure surface — only do this if core flow is solid with time to spare.

Resolve images server-side right after block generation, before returning the chapter to the frontend (don't make the frontend wait on a separate round-trip per image).

---

## 7. API Endpoints (Litestar)

```
POST   /courses                      → create course (topic, level, language) → returns course + chapter list
GET    /courses/{course_id}          → get course + chapter summaries
POST   /courses/{course_id}/chapters/{chapter_id}/generate
                                      → generates & returns full Chapter content
POST   /courses/{course_id}/chapters/{chapter_id}/edit
                                      → body: {prompt} → returns revised Chapter
POST   /quiz/evaluate                → body: {question, sample_answer, grading_rubric, user_answer}
                                      → returns {verdict, feedback}
```

Stream chapter generation via SSE or chunked response if time allows — big demo win (content appearing live) for relatively low added complexity, since you're already calling the LLM with streaming enabled.

---

## 8. Frontend (SvelteKit) Structure

```
/                          → topic/level/language input screen
/course/[id]               → chapter list (sidebar or grid)
/course/[id]/chapter/[cid] → chapter view: renders blocks in order, edit prompt box at bottom
```

**Block renderer components** (one Svelte component per `ContentBlock.type`):

- `TextBlock.svelte` — markdown renderer (use a lightweight markdown-it/marked + sanitize)
- `ImageBlock.svelte`
- `QuizMcBlock.svelte`
- `QuizFreeBlock.svelte`
- `FlashcardsBlock.svelte`

A single `ChapterView.svelte` iterates `blocks` and dispatches to the right component by `type` — this is the whole "artifact" system, no sandboxing needed since blocks are structured data, not executable code.

---

## 9. Non-Goals (explicitly out of scope for MVP)

- User accounts / auth
- Saving/persisting courses across sessions (in-memory or simple DB row is fine, no need for user-scoped storage)
- Course sharing/export
- Editing chapter list after generation (regenerating chapters, reordering, deleting)
- Progress tracking / spaced repetition
- More than 3 interaction types
- Arbitrary code execution or LLM-generated executable UI

---

## 10. Suggested Build Order (fits ~4 hours)

1. Data schemas + Litestar endpoints returning mocked/static JSON (get contracts right first)
2. Topic/level/language input → chapter-list generation (real LLM call)
3. Chapter generation (real LLM call) → render `text` + `image` blocks only
4. Add `quiz_mc` and `flashcards` block renderers
5. Add `quiz_free` block + `/quiz/evaluate` endpoint
6. Add edit-via-prompt flow
7. Polish: streaming, loading states, pick final demo topic, test end-to-end in both languages

