# Core Backend — tin-yu-mal

Hackathon MVP: **AI course outline + module content** (Burmese/English) with fixed interactive JSON types, powered by the **Cursor SDK**.

## Pitch vs MVP

| Big idea (slide) | Built now |
| --- | --- |
| Full adaptive course platform | Topic → outline → one module live |
| Claude-style freeform artifacts | Fixed types: `quiz`, `multiple_choice`, `flashcards` |
| Auth, save progress, history | JWT exists but `/courses` is public for the demo |
| Images / diagrams / simulations | Text sections only; image slot = future |

**Complexity is a depth dial**, not just tone:

- Beginner → 6 modules, analogies, guided interactives  
- Intermediate → 5 modules  
- Advanced → 4 modules, denser, fewer hints  

**Killer demo topic:** “How neural networks work” (also in `/courses/suggestions`).

## Stack

- Litestar + JWT (optional for courses)
- SQLAlchemy async + Postgres
- SAQ + Redis
- **Cursor SDK** (`AsyncAgent.prompt`, `tools=[]`) for outline/module JSON
- Scalar OpenAPI UI

## Quick start

```bash
cd core-backend
cp .env.example .env
# set CURSOR_API_KEY from https://cursor.com/dashboard/integrations
docker compose up --build
```

Or run the API locally (often easier for the Cursor local bridge):

```bash
docker compose up postgres redis -d
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/schema/scalar  

## Course API (frontend contract)

### Quick prompts

`GET /courses/suggestions?language=en|my`

### 1) Generate outline

`POST /courses/outline`

```json
{
  "topic": "How neural networks work",
  "level": "beginner",
  "language": "en"
}
```

→ `{ title, topic, level, language, chapters: [{ index, title, summary }] }`

### 2) Generate module (after user picks a chapter)

`POST /courses/modules/generate`

```json
{
  "topic": "How neural networks work",
  "level": "beginner",
  "language": "en",
  "course_title": "…",
  "chapter": { "index": 1, "title": "…", "summary": "…" }
}
```

→ `{ title, level, language, sections: ["…"], interactive: { type: "quiz"|"multiple_choice"|"flashcards", … } }`

Interactive shapes:

- `quiz`: `instruction`, `expected_answer`, optional `hint`
- `multiple_choice`: `instruction`, `options[]`, `correct_index`
- `flashcards`: `cards: [{ front, back }]`

## Auth (future-facing)

`POST /auth/login` → Bearer token for `/auth/me` and `/tasks/*`. Course routes are excluded for the live demo.
