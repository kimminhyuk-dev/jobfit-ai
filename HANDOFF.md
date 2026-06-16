# HANDOFF

Keep this file current after each agent task. Do not record `.env` values, API keys, tokens, or secrets.

## Project

- Name: `jobfit-ai`
- Goal: AI-assisted resume and job-posting matching platform.
- Current branch: `codex-resume-api-hardening`
- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Pydantic v2
- Frontend: Next.js 16 App Router, React 19, TypeScript, Tailwind CSS v4, TanStack Query, React Hook Form, Zod
- AI: OpenAI API for interview practice, Gemini fallback for resume parsing, planned sentence-transformers + pgvector matching

## Current State

The app is now a 3-role demo platform:

- `USER`: job seeker. Can manage profile/resumes, browse jobs, send a resume to a job, view own application history, and practice resume-based interviews.
- `COMPANY`: company account. Auto-provisioned for ingested job postings and can log in by email or 10-digit business number. Can view received applications on `/company/dashboard`.
- `ADMIN`: admin account. Can manage categories/posts/users/resumes/jobs and run selected collection jobs. `users.admin_level` supports `A`, `B`, `C`; only A-level enforcement is currently implemented for ALIO collection.

## Major Features Implemented

### Authentication And Profile

- JWT access token and refresh token cookie flow.
- Login portal split:
  - `/login`: USER only.
  - `/company/login`: COMPANY and ADMIN.
- Root redirect sends ADMIN to `/admin/dashboard`, COMPANY to `/company/dashboard`, USER to `/user/dashboard`.
- User profile includes optional `birth_date`, `phone`, `gender`, `zipcode`, `address1`, `address2`, and `tech_stack`.
- Daum/Kakao postcode lookup is used on the frontend without an API key.

### Resume And Interview Practice

- Resume upload/list/detail/file/delete endpoints are implemented.
- Parsed resume data includes structured projects and cover letter sections.
- OpenAI-based interview practice is implemented:
  - Session creation generates and stores exactly 5 questions once.
  - Session lookup returns saved questions and answers without calling OpenAI.
  - Answer submission evaluates one answer at a time.
  - OpenAI Web Search is not used.
  - Official references come only from server-side reference material.
- Active endpoints:
  - `POST /resumes/{resume_id}/interview-sessions`
  - `GET /resumes/{resume_id}/interview-sessions/{session_id}`
  - `POST /resumes/{resume_id}/interview-questions/{question_id}/answer`

### Jobs And Applications

- `GET /jobs` supports pagination and filters: `source`, `keyword`, code filters, `data_source`, `status`, `region`, `education`, `employment_type`, `ncs_category`.
- `GET /jobs/filter-options` returns data-derived filter choices.
- `GET /jobs/{job_id}` returns a single posting with `raw_content`.
- User job list is a full-width list; job detail is `/user/jobs/{jobId}`.
- "이력서 보내기" creates an `applications` row.
- Duplicate active application per `(user_id, job_id)` is blocked.
- User application page exists at `/user/applications`.
- Active endpoints:
  - `POST /applications`
  - `GET /applications/me`

### Company Platform

- `companies` table links one company record to one `users.role = COMPANY` login account.
- Company dedupe key is `bn:{digits}` when `business_number` exists, else `nm:{company_name}`.
- Company accounts are auto-created on job ingestion and also ensured at application time.
- Demo company accounts use synthetic emails under `company.jobfit.local` and the demo password convention `admin1234`. This is portfolio/demo-only and not production safe.
- Company dashboard endpoint:
  - `GET /company/dashboard`

### Admin

- Admin user list/detail supports role filters and role-specific search fields.
- Admin category route `GET /admin/categories` shows inactive categories. Public `GET /categories` still returns active categories only.
- ALIO manual collection requires A-level admin.
- Admin jobs page accepts ALIO keyword/start page/max pages/page size.
- Deeper A/B/C account-management actions, such as granting B/C or deleting accounts, are still pending.

### Demo Data

- `backend/app/scripts/seed_demo_accounts.py` creates deterministic demo admin/user/company accounts.
- `backend/app/scripts/generate_mock_work24_jobs.py` generates 100 deterministic Work24-shaped mock postings.
- `backend/data/mock_work24_jobs.json` contains generated mock jobs.
- Mock company business numbers use the Korean business-number checksum rule.

## Database

Current important migrations:

- `i1j2k3l4m5n6_add_resume_interview_practice_tables.py`
- `j2k3l4m5n6o7_add_companies_admin_level_applications.py`
- `k3l4m5n6o7p8_add_user_profile_fields.py`

Important tables:

- Auth/users: `users`, `refresh_tokens`
- Content: `categories`, `posts`
- Jobs: `job_postings`, `job_sources`, `batch_job_runs`, `common_code_groups`, `common_codes`
- Resume: `resumes`, `resume_projects`, `resume_cover_letter_sections`
- Interview: `resume_interview_sessions`, `resume_interview_questions`, `resume_interview_answers`
- Company/applications: `companies`, `applications`

## Main Files Changed In Current Work

Backend:

- `backend/app/api/applications.py`
- `backend/app/api/company.py`
- `backend/app/api/jobs.py`
- `backend/app/api/admin_jobs.py`
- `backend/app/api/admin_users.py`
- `backend/app/api/categories.py`
- `backend/app/api/deps.py`
- `backend/app/models/company.py`
- `backend/app/models/application.py`
- `backend/app/models/user.py`
- `backend/app/repositories/application_repository.py`
- `backend/app/repositories/company_repository.py`
- `backend/app/repositories/job_posting_repository.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/schemas/application.py`
- `backend/app/schemas/company.py`
- `backend/app/schemas/admin_user.py`
- `backend/app/schemas/user.py`
- `backend/app/services/application_service.py`
- `backend/app/services/company_provisioning_service.py`
- `backend/app/services/company_service.py`
- `backend/app/services/job_posting_service.py`
- `backend/app/scripts/seed_demo_accounts.py`
- `backend/app/scripts/generate_mock_work24_jobs.py`

Frontend:

- `frontend/src/screens/LoginPage.tsx`
- `frontend/src/screens/SignupPage.tsx`
- `frontend/src/screens/user/DashboardPage.tsx`
- `frontend/src/screens/user/JobsPage.tsx`
- `frontend/src/screens/user/ApplicationsPage.tsx`
- `frontend/src/screens/user/ProfilePage.tsx`
- `frontend/src/screens/user/ResumesPage.tsx`
- `frontend/src/screens/admin/AdminUsersPage.tsx`
- `frontend/src/screens/admin/AdminJobsPage.tsx`
- `frontend/src/app/company/login/page.tsx`
- `frontend/src/app/company/dashboard/page.tsx`
- `frontend/src/app/user/jobs/[jobId]/page.tsx`
- `frontend/src/app/user/applications/page.tsx`
- `frontend/src/components/jobs/ApplyModal.tsx`
- `frontend/src/components/profile/AddressFields.tsx`
- `frontend/src/components/profile/TechStackInput.tsx`
- `frontend/src/components/ui/Toast.tsx`
- `frontend/src/components/auth/RequireAuth.tsx`
- `frontend/src/components/layout/UserLayout.tsx`
- `frontend/src/api/applications.ts`
- `frontend/src/api/company.ts`
- `frontend/src/api/jobs.ts`
- `frontend/src/api/admin.ts`
- `frontend/src/api/auth.ts`
- `frontend/src/api/client.ts`
- `frontend/src/api/types.ts`

## Verification

Most recent checks completed:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd backend; .\.venv\Scripts\python.exe -c "from app.main import app; print(len(app.routes)); print([r.path for r in app.routes if 'company' in r.path or 'applications' in r.path])"`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `git diff --check`
- Replacement-character search across `frontend/src`, `backend/app`, `backend/alembic`, and `HANDOFF.md`

All blocking checks passed. `git diff --check` only prints line-ending warnings in this workspace.

## Known Remaining Work

- Company self-signup, company layout beyond the current dashboard, and optional company job posting are not implemented.
- Full admin A/B/C account-management actions are not implemented.
- `frontend/src/screens/user/MatchesPage.tsx` still uses old mock matching stats.
- Actual vector embedding/matching with sentence-transformers + pgvector is planned but not implemented.
- Work24 public API integration remains constrained by API approval; mock and ALIO flows are available for demo/development.
