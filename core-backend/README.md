# Core Backend

Litestar API with plain SQLAlchemy (Postgres), SAQ workers (Redis), and JWT auth for a single user type.

## Stack

- **Litestar** — ASGI API
- **SQLAlchemy 2.0 async** + **asyncpg** — Postgres (no Advanced Alchemy)
- **litestar-saq** — background jobs via Redis
- **JWT** — `Authorization: Bearer <token>` for frontend calls
- **Docker Compose** — api, worker, postgres, redis

## Quick start

```bash
cd core-backend
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- OpenAPI: http://localhost:8000/schema
- Health: http://localhost:8000/health

Bootstrap admin (from `.env`):

- email: `admin@example.com`
- password: `changeme`

## Auth flow (frontend)

1. `POST /auth/login` with `{ "email", "password" }` → `{ "access_token", "token_type": "Bearer" }`
2. Call protected routes with header `Authorization: Bearer <access_token>`
3. `GET /auth/me` returns the current user

## Local (without Docker app)

Infra only:

```bash
docker compose up postgres redis
```

Then:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
export DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/app
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=dev-secret
uvicorn app.main:app --reload
# separate terminal
litestar --app app.main:app workers run
```

## Sample job

Authenticated `POST /tasks/sample` enqueues a demo SAQ job on the `default` queue.
