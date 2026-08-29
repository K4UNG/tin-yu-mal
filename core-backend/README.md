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

## Course API (frontend contract — SPECS.md)

### Create course + chapter list

`POST /courses`

```json
{ "topic": "How neural networks work", "level": "beginner", "language": "en" }
```

→ `{ id, topic, level, language, created_at, chapters: [{ id, index, title, description, status }] }`

`status` starts as `not_generated` for every chapter.

### Get course

`GET /courses/{course_id}`

### Uploads (MinIO)

`POST /uploads` — multipart field `file` → `{ id, filename, content_type, size_bytes, has_text, created_at }`

`GET /uploads/{file_id}`

Then create a course with those files:

```json
{
  "topic": "How neural networks work",
  "level": "beginner",
  "language": "en",
  "file_ids": ["<upload-uuid>"]
}
```

Extracted text (txt/md/json/pdf) is truncated and injected into the chapter-list prompt. MinIO console: http://localhost:9001 (`minio` / `minio12345`).

## Auth (future-facing)

`POST /auth/login` → Bearer token for `/auth/me` and `/tasks/*`. Course routes are excluded for the live demo.
