# JobFit AI

AI-assisted resume and job-posting matching platform built as a portfolio/demo project.

JobFit AI helps job seekers manage resumes, browse job postings, send a resume to a posting, track applications, and practice interview questions generated from their parsed resume. It also ships company and admin areas so the demo can show a full end-to-end application flow across three roles.

## Roles

| Role | What it does |
|---|---|
| `USER` | Job seeker. Manage profile and resumes, browse jobs, send a resume to a posting, track applications, and practice resume-based interviews. |
| `COMPANY` | Company account. Auto-provisioned from ingested postings, logs in by email or 10-digit business number, and reviews received applications on a dashboard. |
| `ADMIN` | Admin account. Manage categories/posts, users, resumes, and jobs, and run selected collection jobs. Supports `admin_level` `A`/`B`/`C` (only A-level ALIO collection is currently enforced). |

## Tech Stack

| Area | Stack |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Pydantic v2 |
| Frontend | Next.js 16 App Router, React 19, TypeScript, Tailwind CSS v4 |
| State / forms | TanStack Query, React Hook Form, Zod |
| UI | shadcn/ui-style components, Tailwind utility classes |
| Auth | JWT access token, HttpOnly refresh token cookie (SHA-256 hash stored in DB) |
| AI | OpenAI API for interview practice, Google Gemini fallback for resume parsing |
| Planned matching | sentence-transformers + pgvector |
| Infra | Docker Compose, GitHub Actions |

## Architecture

The backend follows a strict layered flow:

```text
api (router) -> service -> repository -> model
```

- `api/` receives requests and returns responses only — no business logic.
- `services/` holds business logic and never queries the DB directly when a repository method exists.
- `repositories/` handle DB access only.
- `models/` (SQLAlchemy ORM) and `schemas/` (Pydantic DTOs) are kept separate.
- `core/` holds config, database/session, security, and errors.

### Authentication

- Access token: JWT, 15 minutes, cookie-based client flow.
- Refresh token: JWT, 14 days, HttpOnly cookie, SHA-256 hash stored in DB.
- Split login portals: `/login` is USER-only, `/company/login` is COMPANY/ADMIN.
- Root redirect routes ADMIN to `/admin/dashboard`, COMPANY to `/company/dashboard`, USER to `/user/dashboard`.

## Main Features

- Auth with signup, login, refresh, logout, current-user, profile update, and account deletion.
- User profiles with optional birth date, phone, gender, address (Daum/Kakao postcode lookup, no API key), and tech stack.
- Resume upload and parsing, including structured projects and cover letter sections.
- OpenAI interview practice:
  - Create an interview session from a parsed resume and persist exactly 5 questions once.
  - Session lookup returns saved questions/answers and never calls OpenAI.
  - Answers are evaluated one at a time.
  - No OpenAI Web Search; official references come only from server-side reference material.
- Job posting list/detail backed by real APIs with pagination and filters (source, keyword, region, education, employment type, NCS category, and more).
- Application flow: a user sends a selected resume to a job; duplicate active applications per `(user_id, job_id)` are blocked.
- Company dashboard for received applications.
- Admin controls for users, resumes, categories/posts, and job collection.
- Demo seeding scripts for accounts and 100 deterministic Work24-shaped mock job postings.

## Important Backend Endpoints

- Auth: `/auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`
- Jobs: `GET /jobs`, `GET /jobs/filter-options`, `GET /jobs/{job_id}`
- Account recovery: `/auth/find-email`, `/auth/company/find-email`, `/auth/password/reset-request`, `/auth/company/password/reset-request`, `/auth/password/reset-confirm`
- Applications: `POST /applications`, `GET /applications/me`, `DELETE /applications/{application_id}`
- Company: `GET /company/dashboard`, `/company/applications/{id}/resume`, `/company/applications/{id}/resume/file`, `/company/applications/{id}/status`, `/company/applications/{id}/interview-email`
- Company jobs: `GET/POST /company/jobs`, `GET/PATCH/DELETE /company/jobs/{job_id}`
- Admin leave: `POST /admin/leave`, `GET /admin/leave/me`, `GET /admin/leave/pending`, and approve/reject/request-change/cancel/cancel-approve/cancel-reject/resubmit endpoints under `/admin/leave/{id}`
- Resumes: `POST /resumes`, `GET /resumes`, `GET /resumes/{id}`, `GET /resumes/{id}/file`, `DELETE /resumes/{id}`
- Interview practice:
  - `POST /resumes/{resume_id}/interview-sessions`
  - `GET /resumes/{resume_id}/interview-sessions/{session_id}`
  - `POST /resumes/{resume_id}/interview-questions/{question_id}/answer`
- Admin: `/admin/stats`, `/admin/users`, `/admin/categories`, `/admin/job-sources/alio/collect`, `/admin/jobs/sources/mock/load`

## Project Structure

```text
jobfit-ai/
├── backend/
│   └── app/
│       ├── api/            # FastAPI routers (request/response only)
│       ├── services/       # business logic
│       ├── repositories/   # DB access
│       ├── models/         # SQLAlchemy ORM
│       ├── schemas/        # Pydantic DTOs
│       ├── core/           # config, database, security, errors
│       ├── prompts/        # server-side AI prompts and references
│       └── scripts/        # demo seeding and mock data generation
├── frontend/
│   └── src/
│       ├── app/            # Next.js App Router routes
│       ├── screens/        # page-level UI
│       ├── components/     # shared UI components
│       ├── api/            # API client and types
│       ├── stores/         # client state
│       └── lib/            # utilities
└── docker-compose.yml
```

## Development

Backend:

```powershell
docker-compose up -d db
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Root helper scripts (run both apps together from the repo root):

```powershell
npm run dev     # backend + frontend concurrently
npm run lint    # frontend lint
npm run build   # frontend build
```

## Verification

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app

cd ..\frontend
npm run lint
npm run build
```

## Notes

- Demo company accounts are auto-created for ingested postings and use synthetic emails plus the demo password convention `admin1234`. This is portfolio/demo-only and not production-safe.
- Do not commit `.env` values, API keys, tokens, or secrets.
- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are intentionally kept in sync; update all three together.
