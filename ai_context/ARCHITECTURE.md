# ARCHITECTURE

## Backend Layers

```text
api -> service -> repository -> model
```

| Layer | Responsibility |
|---|---|
| `api/` | FastAPI routers, dependencies, request/response mapping |
| `services/` | Business rules and workflow orchestration |
| `repositories/` | SQLAlchemy queries and persistence |
| `models/` | SQLAlchemy ORM models |
| `schemas/` | Pydantic DTOs, separate from ORM models |
| `core/` | Config, database/session, security, exceptions, error codes |
| `prompts/` | Server-side AI prompt/reference material |

Rules:

- Keep business logic out of routers.
- Use repository methods when one exists instead of direct service-level queries.
- Use `get_db`/`deps.py` for DB sessions.
- Use `Settings` from `core/config.py` for environment values.
- Do not log secrets, tokens, request auth headers, or `.env` values.

## Frontend Structure

```text
src/app/          Next.js App Router routes
src/screens/      Page-level UI and data composition
src/components/   Reusable layout, feature, and UI components
src/api/          API client modules and shared types
src/stores/       Auth context/store
src/lib/          Shared utilities
```

Important routes:

- `/login`: USER login
- `/company/login`: COMPANY/ADMIN login
- `/user/dashboard`
- `/user/jobs`
- `/user/jobs/[jobId]`
- `/user/applications`
- `/user/resumes`
- `/user/profile`
- `/company/dashboard`
- `/admin/dashboard`
- `/admin/users`
- `/admin/jobs`
- `/admin/categories`

## Auth Flow

- Access token: short-lived JWT.
- Refresh token: HttpOnly cookie, server stores SHA-256 hash.
- Frontend axios client uses `withCredentials: true`.
- Refresh interceptor calls `/auth/refresh` on 401.
- System errors only, such as network failures or HTTP 500+, dispatch the global toast event.

## Main Database Tables

| Table | Purpose |
|---|---|
| `users` | USER, COMPANY, ADMIN accounts plus optional profile/admin fields |
| `refresh_tokens` | Hashed refresh tokens |
| `categories`, `posts` | Q&A/community content |
| `job_postings` | Job postings from ALIO, mock, manual, or other sources |
| `job_sources` | Collection source status |
| `batch_job_runs` | Collection run history |
| `common_code_groups`, `common_codes` | ALIO/common codes |
| `resumes` | Resume metadata, file metadata, parsed JSON |
| `resume_projects` | Structured resume projects |
| `resume_cover_letter_sections` | Structured cover letter/self-introduction sections |
| `resume_interview_sessions` | Interview practice session |
| `resume_interview_questions` | Persisted interview questions |
| `resume_interview_answers` | Evaluated answers |
| `companies` | Company identity linked to `users.role = COMPANY` |
| `applications` | User resume submissions to job postings/companies |

## Company Provisioning

- Company dedupe key:
  - `bn:{digits}` if business number exists.
  - `nm:{company_name}` otherwise.
- Ingested postings ensure a company account after posting commit.
- Application flow also ensures company account so old postings can receive applications.
- Demo login uses synthetic email/domain and the demo password convention.
