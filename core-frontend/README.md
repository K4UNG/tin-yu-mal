# Core Frontend

Svelte 5 + SvelteKit app. Auth functions (axios + TanStack Query) talk to `core-backend`; no login UI yet.

## Quick start

```bash
cd core-frontend
cp .env.example .env
npm install
npm run dev
```

- App: http://localhost:5173
- API (default): http://localhost:8000

## Auth functions

`POST /auth/login` → store JWT → `GET /auth/me` with `Authorization: Bearer <token>`.

```ts
import { login, getMe, logout } from '$lib/api/auth';
import { createLoginMutation, createMeQuery, createLogoutMutation } from '$lib/api/queries.svelte';
```

Call the `create*` helpers from a component `<script>` (they need QueryClient context from the root layout).
