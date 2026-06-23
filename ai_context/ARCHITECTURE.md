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
- `/company/jobs`
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
| `application_match_scores` | Stored deterministic application match scores |
| `email_verifications` | Account-recovery verification codes and rate-limit state |
| `roles`, `permissions`, `role_permissions`, `user_roles` | RBAC role and permission graph |
| `teams` | Admin team grouping for leave approval lines |
| `admin_leave_requests` | Admin leave requests and approval state |
| `leave_balances` | Per-admin yearly leave balance counters |

## Admin RBAC And Leave Approval

- Existing `users.role` and `users.admin_level` gates remain in place for existing admin features.
- New leave APIs use `require_permission("LEAVE_REQUEST")` and `require_permission("LEAVE_APPROVE")`.
- A-level admins map to `SUPER_ADMIN`; B-level admins map to both `TEAM_LEAD` and `ADMIN_STAFF`; C-level and null-level admins map to `ADMIN_STAFF`.
- Demo admin teams are seeded so B-level admins are team `LEAD`s and C-level admins are team `MEMBER`s.
- Approval lines are one step for now: `MEMBER` -> same-team `LEAD`, `LEAD` -> `SUPER_ADMIN`, `SUPER_ADMIN` -> another `SUPER_ADMIN`.
- A requester can never approve their own leave request.

## Company Provisioning

- Company dedupe key:
  - `bn:{digits}` if business number exists.
  - `nm:{company_name}` otherwise.
- Ingested postings ensure a company account after posting commit.
- Application flow also ensures company account so old postings can receive applications.
- Demo login uses synthetic email/domain and the demo password convention.

## Company Platform

- `/company/dashboard` shows received applications, unread counts, application status summaries, and stored match-score data.
- `/company/jobs` lets companies manage their own manual postings and view linked external postings.
- Manual company postings can be created, edited, hidden/deleted, and restored through company-owned APIs.
- Externally collected postings are read-only for company users.
- Companies can view applicant resume files, mark applications as `REJECTED`, and send interview invitation emails that move applications to `INTERVIEW` only after the email send succeeds.
