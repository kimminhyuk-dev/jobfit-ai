# Agent Instructions for jobfit-ai

`AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are identical copies. When one changes, update all three together.

## 1. Project Overview

- Project: `jobfit-ai`
- Goal: AI-assisted resume and job-posting matching platform.
- First step for every task: read root `HANDOFF.md`.

## 2. Tech Stack

| Area | Stack |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Pydantic v2, python-jose, passlib[bcrypt] |
| Frontend | React 19, Next.js 16 App Router, TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query, React Hook Form + Zod |
| AI/ML | OpenAI API for interview practice, Google Gemini API for resume parsing fallback, planned sentence-transformers + pgvector |
| Infra | Docker Compose, GitHub Actions |

## 3. Layered Architecture

```text
api (router) -> service -> repository -> model
```

- `api/`: receive requests and return responses only. No business logic.
- `services/`: business logic. No direct DB queries when a repository method exists.
- `repositories/`: DB access only. No business logic.
- `models/`: SQLAlchemy ORM, separated from schemas.
- `schemas/`: Pydantic DTOs, separated from ORM models.
- `core/`: config, database/session, security, errors.

## 4. Auth

- Access token: JWT, 15 minutes, `Authorization: Bearer` and/or cookie depending on client flow.
- Refresh token: JWT, 14 days, HttpOnly cookie, SHA-256 hash stored in DB.
- Roles: `users.role` is `USER` or `ADMIN`.
- Category and Q&A post create/update/delete are ADMIN-only.

## 5. Coding Rules

- Python follows PEP 8, snake_case for functions/variables, PascalCase for classes.
- Routes using synchronous SQLAlchemy sessions should be `def`; use `async def` only when async I/O is needed.
- DB sessions must come from `deps.py` / `get_db`.
- Environment variables must be accessed through `core/config.py` / `Settings`.
- Never write or print `.env` values, secrets, API keys, or tokens.

## 6. Development Commands

```powershell
docker-compose up -d db
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m compileall app
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## 7. Agent Workflow Rules

1. Read `HANDOFF.md` before starting work.
2. Check `git status --short` before editing.
3. Do not revert user changes.
4. Modify only files directly related to the request.
5. Preserve existing unrelated functionality and decisions.
6. Never expose `.env` values, secrets, or tokens.
7. Update `HANDOFF.md` after completing work.
8. Before creating a new file, check whether an equivalent file already exists.
9. Commit message style: `feat/fix/refactor/docs/chore(scope): description`.
10. Keep `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` synchronized.

## 8. Current AI Feature Notes

- Interview practice uses OpenAI, not Claude.
- OpenAI calls are user-triggered only:
  - session creation generates and stores 5 questions once.
  - answer submission evaluates one answer at a time.
- Session lookup must not call OpenAI.
- Do not use OpenAI Web Search tools for this feature.
- Official references must come only from server-side reference material.
- Do not invent model documentation URLs or official references.
