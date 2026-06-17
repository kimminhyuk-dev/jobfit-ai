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
- Signup page now uses production-style required markers (`*`) for required account fields, adds password confirmation, shows toast/error-bubble feedback on validation failures, and scrolls/focuses the first invalid field (for example, a 7-character password focuses the password field with the 8-character rule visible).
- Login portal split:
  - `/login`: USER only.
  - `/company/login`: COMPANY and ADMIN.
- The frontend sends the active login portal to `/auth/login`; the backend refuses mismatched roles before issuing cookies. A wrong-role account therefore behaves like a failed login and does not create a temporary session or trigger browser password-success warnings. The login screen also rejects any mismatched-role response defensively and shows portal-specific invalid-login messages. Role checks normalize role strings before comparison so `ADMIN` accounts can log in through `/company/login` while `USER` accounts remain blocked there.
- Root redirect sends ADMIN to `/admin/dashboard`, COMPANY to `/company/dashboard`, USER to `/user/dashboard`.
- Login page supports "아이디 저장" and "자동 로그인" via client `localStorage` (`frontend/src/lib/loginPrefs.ts`). Both options always render unchecked by default, even if older saved preferences exist; login/signup pages skip cookie-based session restore so they do not call `/auth/me` or `/auth/refresh` while showing the login form. Protected pages still restore the existing cookie session so a successful login is not cleared during navigation.
- Login inputs use floating labels ("아이디" / "비밀번호") on the field border; portal id field accepts email or business number.
- User profile includes optional `birth_date`, `phone`, `gender`, `zipcode`, `address1`, `address2`, and `tech_stack`.
- Daum/Kakao postcode lookup is used on the frontend without an API key.

### Resume And Interview Practice

- Resume upload/list/detail/file/delete endpoints are implemented.
- New resume uploads accept `PDF, PNG, JPG, JPEG, GIF` up to 10MB. DOCX is intentionally blocked instead of attempting browser-native preview, matching the job-board pattern of using an internal resume view plus downloadable/preview-safe attachments.
- Parsed resume data includes structured projects and cover letter sections.
- `/user/resumes` no longer auto-loads DOCX originals into an iframe. PDF/TXT legacy originals use the file preview path when preview-safe; PNG/JPG/JPEG/GIF show as image previews; legacy DOCX falls back to parsed text/parsed data so opening the page does not trigger a browser download.
- `GET /resumes/{resume_id}/file` returns the original file with inline content disposition for preview-friendly file types.
- Frontend API errors are sanitized into user-facing messages; system/network failures no longer emit a global "server connection" toast. User login failures show "아이디 또는 비밀번호를 확인해주세요."; company/admin login failures show "사업자등록번호 또는 이메일을 확인해주세요."
- External webfont imports were removed in favor of a stable system font stack to reduce font/layout shift during refresh and page navigation.
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
- The `l4m5n6o7p8q9` migration adding `applications.viewed_at` has been applied locally; missing this column caused `/applications` to fail during resume submission and appear as a browser CORS error.
- User application page exists at `/user/applications`.
- Application status flow is `SUBMITTED`(지원 완료) → `VIEWED`(이력서 열람); a company opening an applicant's resume flips the status to VIEWED and stamps `applications.viewed_at` once. The applicant sees the viewed state and viewed time.
- `DELETE /applications/{id}` changes the user's own application to `CANCELED` and marks it inactive for duplicate checks; the canceled row still appears in `GET /applications/me`, while the partial unique index lets the user re-apply to the same job afterward.
- User-side UI is wired: the job list (`/user/jobs`) and job detail show "지원완료" with an "이미 지원한 공고입니다" toast when the job already has a non-canceled item in `GET /applications/me`; canceled items show as "지원취소" in `/user/applications` and do not block re-application. `ApplyModal` also toasts on the `APPLICATION_001` conflict. `/user/applications` shows a "지원취소" button (SUBMITTED/VIEWED only) that calls `DELETE /applications/{id}` and refetches.
- Active endpoints:
  - `POST /applications`
  - `GET /applications/me`
  - `DELETE /applications/{application_id}` (cancel)

### Company Platform

- `companies` table links one company record to one `users.role = COMPANY` login account.
- Company dedupe key is `bn:{digits}` when `business_number` exists, else `nm:{company_name}`.
- Company accounts are auto-created on job ingestion and also ensured at application time.
- Company dashboard self-heals missing `companies` rows for active `COMPANY` users by creating a minimal company profile, so a valid company login opens an empty dashboard instead of failing with `COMPANY_NOT_FOUND`.
- Company dashboard UI now includes unread-application alerting, status summary, recent applicant overview, operational status, refresh action, and a richer empty state instead of only showing the applicant table.
- The applicant table has an "이력서 보기" action that opens `ApplicantResumeModal`; opening it calls `GET /company/applications/{id}/resume`, which marks the application VIEWED and returns resume metadata plus parsed summary data. The modal then loads `GET /company/applications/{id}/resume/file` and shows the original PDF/image in a document-style preview, with a download button for the same original file. After viewing, the dashboard query is invalidated so the unread alert (`pending_count` = unviewed/SUBMITTED count) decreases.
- The resume modal has a "면접 이메일 보내기" button that is a placeholder only (shows a "준비 중" toast); no email is sent yet.
- Company posting management lives at `/company/jobs` (linked from the dashboard header). Companies can create/edit/delete their own `source="MANUAL"` postings, hide/unhide them with status `HIDDEN`, and view all postings matched by `business_number`/`company_name`. Externally collected postings are read-only (`editable=false`). Public `GET /jobs` excludes `HIDDEN` postings unless explicitly filtered by status.
- Demo company accounts use synthetic emails under `company.jobfit.local` and the demo password convention `admin1234`. This is portfolio/demo-only and not production safe.
- Company endpoints:
  - `GET /company/dashboard`
  - `GET /company/applications/{application_id}/resume` (view applicant resume + mark VIEWED)
  - `GET /company/applications/{application_id}/resume/file` (preview/download original resume file)
  - `GET /company/jobs`, `POST /company/jobs`, `GET /company/jobs/{job_id}`, `PATCH /company/jobs/{job_id}`, `DELETE /company/jobs/{job_id}`

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
- `backend/app/api/resumes.py`
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
- `frontend/src/app/company/jobs/page.tsx`
- `frontend/src/components/company/ApplicantResumeModal.tsx`
- `frontend/src/components/company/CompanyJobDetailModal.tsx`
- `frontend/src/components/company/CompanyJobFormModal.tsx`
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
- `frontend/src/lib/loginPrefs.ts`
- `frontend/src/stores/authStore.tsx`

## Verification

Most recent checks completed:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd backend; .\.venv\Scripts\python.exe -c "from app.main import app; print(len(app.routes)); print([r.path for r in app.routes if 'company' in r.path or 'applications' in r.path])"`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `git diff --check`
- Replacement-character search across `frontend/src`, `backend/app`, `backend/alembic`, and `HANDOFF.md`

Latest resume preview fix verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

Latest signup validation/style fix verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `git diff --check`
- In-app Browser verification was attempted but the Browser node runtime failed in this Windows sandbox (`spawn setup refresh`). The Next dev server is running at `http://localhost:3000/signup` after a sandbox-approved `npm run dev -- --hostname 127.0.0.1 --port 3000`.

Latest file-format/error/font handling verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

Latest role-aware login fix verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

Latest applications/CORS masking fix verified:

- `cd backend; .\.venv\Scripts\alembic.exe upgrade head`
- `cd backend; .\.venv\Scripts\python.exe -c "from app.core.database import engine; from sqlalchemy import inspect; cols=[c['name'] for c in inspect(engine).get_columns('applications')]; print('viewed_at' in cols); print('company_id' in cols)"`
- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `curl.exe -i -X OPTIONS http://localhost:8004/applications -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type"`

Latest company resume preview/download and posting hide-management verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

Latest application cancellation status fix verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

All blocking checks passed. `git diff --check` only prints line-ending warnings in this workspace.

## Known Remaining Work

- Company self-signup and broader company layout beyond the current dashboard/jobs screens are not implemented.
- Full admin A/B/C account-management actions are not implemented.
- `frontend/src/screens/user/MatchesPage.tsx` still uses old mock matching stats.
- Actual vector embedding/matching with sentence-transformers + pgvector is planned but not implemented.
- Work24 public API integration remains constrained by API approval; mock and ALIO flows are available for demo/development.
