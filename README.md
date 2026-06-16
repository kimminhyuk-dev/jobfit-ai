# JobFit AI

AI-assisted resume and job-posting matching platform for a portfolio/demo environment.

JobFit AI helps job seekers manage resumes, browse job postings, send a resume to a posting, track applications, and practice interview questions generated from their parsed resume. It also includes company and admin areas so the demo can show a full application flow.

## Current Status

Active development. The current app is a 3-role platform:

- `USER`: job seeker pages for dashboard, jobs, applications, resumes, profile, and interview practice.
- `COMPANY`: company login and dashboard for received applications.
- `ADMIN`: admin dashboard, categories/posts, user/resume management, job collection controls.

## Tech Stack

| Area | Stack |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Pydantic v2 |
| Frontend | Next.js 16 App Router, React 19, TypeScript, Tailwind CSS v4 |
| State/forms | TanStack Query, React Hook Form, Zod |
| UI | shadcn/ui-style components, Tailwind utility classes |
| Auth | JWT access token, HttpOnly refresh token cookie |
| AI | OpenAI API for interview practice, Gemini fallback for resume parsing |
| Planned matching | sentence-transformers + pgvector |
| Infra | Docker Compose, GitHub Actions |

## Main Features

- Auth with signup, login, refresh, logout, current-user, profile update, and account deletion.
- Split login portals:
  - `/login` for normal users.
  - `/company/login` for company and admin accounts.
- Resume upload and parsing, including structured projects and cover letter sections.
- OpenAI interview practice:
  - Create an interview session from a parsed resume.
  - Persist exactly 5 questions.
  - Evaluate answers one at a time.
  - Never call OpenAI during session lookup.
  - Do not use OpenAI Web Search.
- Job posting list/detail with filters and real backend APIs.
- Application flow through "이력서 보내기".
- User application history at `/user/applications`.
- Company dashboard at `/company/dashboard`.
- Admin user/resume/category/job controls.
- Demo seeding scripts for accounts and mock Work24-shaped job postings.

## Important Backend Endpoints

- Auth: `/auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`
- Jobs: `GET /jobs`, `GET /jobs/filter-options`, `GET /jobs/{job_id}`
- Applications: `POST /applications`, `GET /applications/me`
- Company: `GET /company/dashboard`
- Resumes: `POST /resumes`, `GET /resumes`, `GET /resumes/{id}`, `GET /resumes/{id}/file`, `DELETE /resumes/{id}`
- Interview practice:
  - `POST /resumes/{resume_id}/interview-sessions`
  - `GET /resumes/{resume_id}/interview-sessions/{session_id}`
  - `POST /resumes/{resume_id}/interview-questions/{question_id}/answer`
- Admin: `/admin/stats`, `/admin/users`, `/admin/categories`, `/admin/job-sources/alio/collect`, `/admin/jobs/sources/mock/load`

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

Root helper scripts:

```powershell
npm run dev
npm run lint
npm run build
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

- Demo company accounts are auto-created for ingested postings and use synthetic emails plus the demo password convention `admin1234`. This is not production-safe.
- Do not commit `.env` values, API keys, tokens, or secrets.
- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are intentionally synchronized.
