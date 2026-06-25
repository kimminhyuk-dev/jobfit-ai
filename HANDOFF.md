# HANDOFF

Keep this file current after each agent task. Do not record `.env` values, API keys, tokens, or secrets.

## ⏭️ RBAC + 휴가 결재 — 진행 상황 / 다음 작업 (Codex 인계)

> 작업 지시서: "정식 RBAC + 휴가 결재" (NIST 표준 RBAC + 근로기준법 제60조 취지의 휴가 결재). Phase 0→3 단계별 승인 방식. 한국어 독스트링, 4-space PEP8, 한자 사용 금지.

### 상태 스냅샷
- **Phase 0 (조사)**: ✅ 완료 (사용자 승인).
- **Phase 1 (RBAC 기반 구조)**: ✅ 완료 + DB 적용 + 검증 완료 (사용자 승인).
- **Phase 2 (휴가 결재)**: ✅ 완료 + DB 적용 + 검증 완료.
- **Phase 3 (화면/API 연결)**: ⏸ 대기 — 관리자 페이지 휴가 신청/결재 화면은 아직 구현 전.

### Phase 1에서 한 일 (이미 DB 적용됨)
- 신규 모델: [models/rbac.py](backend/app/models/rbac.py) (`Role`/`Permission`/`RolePermission`/`UserRole` + 역할/권한 코드 상수), [models/team.py](backend/app/models/team.py) (`Team` + `LEAD`/`MEMBER`).
- 신규 리포지토리: [repositories/rbac_repository.py](backend/app/repositories/rbac_repository.py) — `user_roles→roles→role_permissions→permissions` 권한 조회.
- 수정: [models/user.py](backend/app/models/user.py) (`team_id` FK + `team_role` 컬럼), [api/deps.py](backend/app/api/deps.py) (`require_permission("CODE")` + 호환 셰임 `_legacy_role_codes`/`get_user_permission_codes`), [alembic/env.py](backend/alembic/env.py) (신규 모델 import).
- 마이그레이션(적용 완료, 단일 head = `r0s1t2u3v4w5`):
  - `q9r0s1t2u3v4_add_rbac_and_team_tables.py` (DDL: 5테이블 + users.team_id/team_role)
  - `r0s1t2u3v4w5_seed_rbac_and_backfill_admins.py` (시드 + 백필)
- 시드된 역할/권한: 역할 `SUPER_ADMIN/TEAM_LEAD/ADMIN_STAFF/OPS_ADMIN`, 권한 `LEAVE_REQUEST/LEAVE_APPROVE/USER_MANAGE/JOB_MANAGE`. 매핑: SUPER_ADMIN=4개 전부, TEAM_LEAD=REQUEST+APPROVE, ADMIN_STAFF/OPS_ADMIN=REQUEST+JOB_MANAGE.
- 무중단 이전: 기존 `users.role`/`admin_level` 컬럼·의존성(`get_current_admin_user`/`get_current_a_admin_user`) **그대로 유지**. 기존 엔드포인트는 RBAC로 이전하지 않음(회귀 0). 신규 기능만 `require_permission` 사용.
- 검증(임시 스크립트로 확인 후 삭제): 권한 없는 USER/C-admin이 `LEAVE_APPROVE` 시도→403 차단, A-admin 통과, 셰임으로 user_roles 없는 ADMIN도 폴백, A-level ALIO 게이트 정상.

### Phase 2 결정 및 적용 결과

- (갱신됨) 데모 ADMIN 244명은 이후 사용자 승인하에 현업 규모 조직(활성 ADMIN 19명)으로 하드 삭제 정리 완료. 아래 "데모 관리자 조직 정리" 절 참고.
- B등급 ADMIN은 `TEAM_LEAD + ADMIN_STAFF` 다중 역할로 보정 완료. B는 `LEAVE_APPROVE`, `LEAVE_REQUEST`, `JOB_MANAGE`를 모두 유지한다.
- `_legacy_role_codes()`도 같은 정책으로 보정 완료: A→`SUPER_ADMIN`, B→`TEAM_LEAD + ADMIN_STAFF`, C/NULL→`ADMIN_STAFF`.
- 데모 팀 3개를 시드하고 B등급 ADMIN을 `LEAD`, C등급 ADMIN을 `MEMBER`로 고르게 배정 완료. A등급은 `SUPER_ADMIN`으로 팀 결재선 밖에 둠.

### 데모 관리자 조직 정리 (현업 규모로 재구성, 사용자 승인)

- 결과 상태: 활성 ADMIN **19명** = SUPER_ADMIN 2 + OPS_ADMIN 1 + (팀 3개 × [TEAM_LEAD 1 + ADMIN_STAFF 4]) 15 + NULL등급 실관리자(`test@test.com`) 1.
- 각 팀: LEAD 1 + MEMBER 4 (이전 27/27 → 1/4). `LEAVE_APPROVE` 보유 = SUPER_ADMIN 2 + TEAM_LEAD 3.
- OPS_ADMIN(`admin007`)은 권한 계열이 `ADMIN_STAFF`와 동일(LEAVE_REQUEST+JOB_MANAGE)하여 레거시 셰임과 충돌하지 않도록 `admin_level='C'`로 둔다. 검증상 OPS는 SUPER 권한(USER_MANAGE/LEAVE_APPROVE)으로 새지 않는다.
- 정리는 데모 관리자 225명 **하드 삭제**. `user_roles`/`refresh_tokens`는 FK `ON DELETE CASCADE`로 함께 정리(orphan 0). 데모 관리자는 공고/지원/게시글/이력서/휴가/회사 데이터에 엮여있지 않아 실데이터 무손상(공고 203·지원 5건 유지). USER/COMPANY 데모 243/243명·`test@test.com`은 미변경.
- 재현/멱등: 두 스크립트가 동일 `ADMIN_ORG` 스펙 공유.
  - [scripts/seed_demo_accounts.py](backend/app/scripts/seed_demo_accounts.py): 관리자는 고정 조직(`ADMIN_ORG`)으로만 시드(USER/COMPANY와 디커플). USER/COMPANY는 `--count-per-role`(기본 243)로 별도 시드. 역할/팀/등급을 목표값으로 동기화하여 재실행해도 중복 0.
  - [scripts/cleanup_demo_admins.py](backend/app/scripts/cleanup_demo_admins.py): 기본 dry-run, `--apply`로만 실제 삭제. `seed_admin_org`로 남길 계정 정규화 후 목표 외 데모 관리자 하드 삭제. 재실행 시 삭제/생성/정규화 0으로 수렴.

### Phase 2 구현 내용

- 테이블: `admin_leave_requests`, `leave_balances`.
- 상태: `PENDING/APPROVED/REJECTED/CANCELED/CANCEL_REQUESTED/CHANGE_REQUESTED`.
- 종류: `ANNUAL`, `AM_HALF`, `PM_HALF`, `SICK`, `FAMILY_EVENT`, `OFFICIAL`, `COMPENSATORY`.
- 결재선: MEMBER→같은 팀 LEAD, LEAD→SUPER_ADMIN, SUPER_ADMIN→다른 SUPER_ADMIN.
- 본인 신청 본인 승인 금지, 정해진 결재자 외 승인 금지.
- 잔여일: 신청 시 `pending_days` 증가/`remaining_days` 감소, 승인 시 `pending_days` 감소/`used_days` 증가, 반려·승인 전 취소 시 복구, 승인 후 취소 승인 시 `used_days` 감소/`remaining_days` 증가, 승인 후 취소 반려 시 `APPROVED`로 복귀하고 잔여일은 유지.
- 일정 변경 요청(직무 분리 유지): 결재자가 PENDING 신청을 승인/반려 대신 `request-change`로 처리하면 별도 상태 `CHANGE_REQUESTED`로 전이하고 사유(`change_request_reason`)를 저장하되 예약 일수(`pending_days`)는 그대로 둔다. 신청자는 `resubmit`으로 날짜/종류/사유를 고쳐 다시 `PENDING`으로 올리거나(잔여 재계산: 기존 예약 환원 후 새 일수 재예약, 연도 교차도 처리), `cancel`로 종료(잔여 복구)한다.
- API 경로는 `/admin/leave-requests/*`에서 `/admin/leave/*`로 통일했다.
  - `POST /admin/leave`
  - `GET /admin/leave/me`
  - `GET /admin/leave/pending`
  - `PATCH /admin/leave/{leave_request_id}/approve`
  - `PATCH /admin/leave/{leave_request_id}/reject`
  - `PATCH /admin/leave/{leave_request_id}/request-change`
  - `PATCH /admin/leave/{leave_request_id}/cancel`
  - `PATCH /admin/leave/{leave_request_id}/cancel-approve`
  - `PATCH /admin/leave/{leave_request_id}/cancel-reject`
  - `PATCH /admin/leave/{leave_request_id}/resubmit`
- Phase 3(화면): 관리자 페이지에 신청 폼/결재함/내 신청내역. 기존 디자인시스템(button.tsx, Alert, Tailwind v4) 사용. 결재함에 "일정 변경 요청", "취소 승인", "취소 반려" 액션, 내 신청내역에 변경 요청 사유 표시 + 재신청 폼 필요.

### 실행/검증 커맨드 (PowerShell)
```powershell
docker-compose up -d db
cd backend; .\.venv\Scripts\Activate.ps1
.\.venv\Scripts\alembic.exe heads          # 단일 head 확인
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m compileall app
# 검증 임시 스크립트는 backend\ 루트에 만들고 실행 후 반드시 삭제(저장소에 남기지 말 것)
```

### 주의
- 작업 시작 전부터 `README.md` / `ai_context/API_SPEC.md` / `ai_context/ARCHITECTURE.md` / `frontend/README.md`가 수정(M) 상태 — **이건 사용자 변경이므로 되돌리지 말 것**.
- AGENTS.md/CLAUDE.md/GEMINI.md 동기화 규칙 유지. 한자 금지. 로그에 개인정보/사유 원문 남기지 말 것.

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
- Account recovery is split out of the login page into real routes: `/find-account` and `/reset-password`. Login pages only link into those routes. The recovery form supports personal/company selection through URL-backed tabs. Personal find-email calls `POST /auth/find-email`; company find-email calls `POST /auth/company/find-email`. Personal password reset calls `POST /auth/password/reset-request`; company password reset calls `POST /auth/company/password/reset-request`; both reuse `POST /auth/password/reset-confirm`.
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
- `POST /applications` is restricted to `USER` accounts; `COMPANY`/`ADMIN` accounts receive 403 instead of creating applications.
- The `l4m5n6o7p8q9` migration adding `applications.viewed_at` has been applied locally; missing this column caused `/applications` to fail during resume submission and appear as a browser CORS error.
- User application page exists at `/user/applications`.
- Application status flow is `SUBMITTED`(지원 완료) → `VIEWED`(이력서 열람); a company opening an applicant's resume flips the status to VIEWED and stamps `applications.viewed_at` once. The applicant sees the viewed state and viewed time.
- Current allowed application statuses are `SUBMITTED`, `VIEWED`, `REJECTED`, `INTERVIEW`, and `CANCELED`. `applications.status` is still a string column, so backend whitelist validation is centralized in the application model/repository and request DTOs. Local data check found 0 `ACCEPTED` rows, and no data conversion was performed.
- `DELETE /applications/{id}` changes the user's own application to `CANCELED` and marks it inactive for duplicate checks; the canceled row still appears in `GET /applications/me`, while the partial unique index lets the user re-apply to the same job afterward.
- User-side UI is wired: the job list (`/user/jobs`) and job detail show "지원완료" with an "이미 지원한 공고입니다" toast when the job already has a non-canceled item in `GET /applications/me`; `VIEWED`, `REJECTED`, `INTERVIEW`, and `CANCELED` have user-facing labels on the dashboard/application history. `ApplyModal` also toasts on the `APPLICATION_001` conflict. `/user/applications` shows a "지원취소" button (SUBMITTED/VIEWED only) that calls `DELETE /applications/{id}` and refetches.
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
- Company dashboard applicant rows and the applicant resume modal include stored matching score data from `application_match_scores`. New applications calculate a deterministic `local-match-v1` score immediately; existing company applications are backfilled lazily when the dashboard or modal is opened. API responses expose score/grade, summary, strengths, gaps, and skill lists; internal calculation evidence stays in the DB and is not returned to the frontend. Scoring tunables live in `match_score_constants.py`; sensitive demographic tokens are excluded from text-similarity scoring.
- Company dashboard can mark an application `REJECTED` through `PATCH /company/applications/{id}/status`; the service reuses the existing "application belongs to this company posting" validation. `INTERVIEW` is intentionally not accepted by this manual endpoint and is set only after a successful interview-email send.
- The resume modal has a wired "면접 이메일 보내기" flow. It opens an in-modal form for interview date/time, address, and optional message; the address defaults to `companies.address` from `GET /company/dashboard` but remains editable. The frontend blocks past date/time selections before calling `POST /company/applications/{id}/interview-email`, and successful sends invalidate dashboard/resume queries so the `INTERVIEW` badge appears.
- Company posting management lives at `/company/jobs` (linked from the dashboard header). Companies can create/edit/delete their own `source="MANUAL"` postings, hide/unhide them with status `HIDDEN`, and view all postings matched by `business_number`/`company_name`. Externally collected postings are read-only (`editable=false`). Public `GET /jobs` excludes `HIDDEN` postings unless explicitly filtered by status.
- Demo company accounts use synthetic emails under `company.jobfit.local` and the demo password convention `admin1234`. This is portfolio/demo-only and not production safe.
- Company endpoints:
  - `GET /company/dashboard`
  - `GET /company/applications/{application_id}/resume` (view applicant resume + mark VIEWED)
  - `GET /company/applications/{application_id}/resume/file` (preview/download original resume file)
  - `PATCH /company/applications/{application_id}/status` (company-owned application, `REJECTED` only for now)
  - `GET /company/jobs`, `POST /company/jobs`, `GET /company/jobs/{job_id}`, `PATCH /company/jobs/{job_id}`, `DELETE /company/jobs/{job_id}`
  - `POST /company/applications/{application_id}/interview-email` (send interview invitation with inline map)

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

### Email / SMTP (migration groundwork)

- Ported the Spring JobFolio `spring.mail.*` mail setup into Python-style config as part of the JobFolio→jobfit-ai migration.
- `backend/.env` already holds Python-style SMTP keys (`SMTP_HOST/PORT/USERNAME/PASSWORD`, `SMTP_AUTH`, `SMTP_USE_TLS`, `SMTP_REQUIRE_TLS`, `SMTP_CONNECTION_TIMEOUT_MS`, `SMTP_TIMEOUT_MS`, `SMTP_WRITE_TIMEOUT_MS`, `SMTP_SSL_TRUST`, `APP_NAME`). `.env` stays gitignored; only `.env.example` documents these with placeholder values. Spring-style keys (`spring.mail.*`) are not used anywhere in code.
- `app/core/config.py` `Settings` now exposes matching snake_case fields (`smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_auth`, `smtp_use_tls`, `smtp_require_tls`, `smtp_connection_timeout_ms`, `smtp_timeout_ms`, `smtp_write_timeout_ms`, `smtp_ssl_trust`). pydantic-settings matches env vars case-insensitively.
- `app/services/email_service.py` is a stdlib `smtplib`-based service (no new dependency). It reads all settings from `config.settings`, converts the ms connection timeout to a seconds socket timeout, applies STARTTLS per `smtp_use_tls`/`smtp_require_tls`, uses `APP_NAME` as the sender display name, and exposes `send_email`, `send_verification_code`, `send_temporary_password`, and `send_found_id_email`. It sends plain text plus table-based HTML alternatives for account-recovery emails. It logs only masked SMTP usernames/recipients and `password loaded: true|false` — never the password, verification code, or temporary password.
- Account-recovery and interview-email features ported from JobFolio are now implemented on top of this mail foundation (see next section). Signup email-verification is still only planned.

### Account Recovery And Interview Email (ported from JobFolio)

Ported from `kimminhyuk-dev/JobFolio` (`/api/join/...` flows) into the jobfit-ai structure. Personal and company account recovery are wired into the login UI, and interview-email sending is wired from the company resume modal.

- New table `email_verifications` (`m5n6o7p8q9r0`): stores password-reset codes as SHA-256 hashes (NOT plaintext — a deliberate security improvement over JobFolio's plaintext `tb_email_verification`), with `purpose`, `expires_at`, `is_used`/`used_at`, plus rate-limit columns `attempt_count` and `last_attempt_at` (`o7p8q9r0s1t2`). Codes are 6-digit, 5-minute TTL.
- `companies.address` column added (`n6o7p8q9r0s1`) as the default interview location for interview emails.
- New public (no-auth) auth endpoints:
  - `POST /auth/find-email`: personal account lookup by name + phone. On match, returns a masked email such as `ab***@example.com` and emails the found id to the user's own address. On no match, returns no `masked_email` and a non-specific no-match message. The 60-second send rate limit remains.
  - `POST /auth/company/find-email`: company account lookup by `users.name` (담당자/대표자명) + 10-digit normalized business number. On match, returns the same masked-email shape as personal find-email and emails the found id to the company account email.
  - `POST /auth/password/reset-request`: send a 6-digit reset code (existence not disclosed).
  - `POST /auth/company/password/reset-request`: company password reset request by `users.name` + business number + email. All three must match before a reset code is issued, but the response keeps account existence undisclosed.
  - `POST /auth/password/reset-confirm`: verify code → generate a temporary password → email it → only then change the password and revoke all refresh tokens. If the email send fails the password is left unchanged (avoids lockout).
- New company application endpoint:
  - `POST /company/applications/{application_id}/interview-email`: COMPANY-only. Sends an interview invitation to the applicant. `interview_at` must be in the future. Interview location comes from the request body or `companies.address`. A Google Maps Static API map is fetched server-side and attached inline (CID, `multipart/related`) so the API key is never exposed in the email; a `https://www.google.com/maps/search/?api=1&query=...` link is included as well. Missing/failed map degrades gracefully (email still sends with the link). After the email service returns successfully, the application status is changed to `INTERVIEW`; send failures do not change the status.
- Phone matching for find-email normalizes both sides to digits (`regexp_replace`), since `users.phone` may be stored with hyphens.
- Account recovery rate limiting is implemented without account locking: find-email and password reset sends are limited to one request per 60 seconds. Password reset confirmation has no 60-second attempt throttle; 5 consecutive failed code attempts expire the active code.
- There is currently no automatic cleanup job for expired `email_verifications` rows; add a maintenance cleanup for rows whose `expires_at` is older than a retention window before exposing this flow at scale.
- Config: `google_maps_api_key` / `google_maps_static_base_url` added to `Settings`; `.env.example` documents `GOOGLE_MAPS_API_KEY` with a placeholder. The mail service also supports inline images (`send_email(..., inline_images=...)`) and `send_found_id_email`. Interview email keeps the Google Maps CID attachment flow but now shares the account-recovery header/footer tone.
- Code/temp-password generation lives in `core/security.py` (`generate_numeric_code`, `generate_temporary_password`, secure-random based). No new dependency added (stdlib `smtplib`/`secrets` + existing `httpx`).
- Reused logic: `account_recovery_service.py` handles both find-email and password reset; `interview_email_service.py` builds/sends the interview email.

### RBAC + Org Structure (Phase 1)

NIST-standard RBAC was introduced as the foundation for an upcoming leave-approval feature. Roll-out is non-breaking: the existing `users.role` / `users.admin_level` columns and their dependencies are kept, existing ADMINs are backfilled, a compatibility shim covers legacy accounts, and only new features use RBAC.

- New tables: `roles`, `permissions`, `role_permissions` (many-to-many), `user_roles` (many-to-many), `teams`. New columns `users.team_id` (FK `teams`, `ON DELETE SET NULL`) and `users.team_role` (`LEAD`/`MEMBER`) for leave approval-line calculation.
- Seeded roles: `SUPER_ADMIN`, `TEAM_LEAD`, `ADMIN_STAFF`, `OPS_ADMIN`. Seeded permissions: `LEAVE_REQUEST`, `LEAVE_APPROVE`, `USER_MANAGE`, `JOB_MANAGE`. Role→permission seed: SUPER_ADMIN=all 4; TEAM_LEAD=LEAVE_REQUEST+LEAVE_APPROVE; ADMIN_STAFF/OPS_ADMIN=LEAVE_REQUEST+JOB_MANAGE.
- Permissions are granted only through roles (NIST principle — no direct user grants). `require_permission("CODE")` in `app/api/deps.py` is the common FastAPI dependency; `RbacRepository` resolves `user_roles → roles → role_permissions → permissions`.
- Backfill migration first assigned existing ADMINs from `admin_level`; Phase 2 then corrected B-level admins to multi-role `TEAM_LEAD + ADMIN_STAFF`. Current mapping is `A → SUPER_ADMIN`, `B → TEAM_LEAD + ADMIN_STAFF`, `C`/`NULL → ADMIN_STAFF`. The compatibility shim (`_legacy_role_codes`) applies the same mapping at request time so ADMIN accounts work even without a `user_roles` row.
- Existing `get_current_admin_user` / `get_current_a_admin_user` (A-level ALIO collection gate) are unchanged. No existing endpoint was migrated to `require_permission` in Phase 1; leave-approval endpoints in Phase 2 will use it.
- Demo team rows are now seeded in Phase 2; B-level admins are team `LEAD`s and C-level admins are team `MEMBER`s.

## Database

Current important migrations:

- `i1j2k3l4m5n6_add_resume_interview_practice_tables.py`
- `j2k3l4m5n6o7_add_companies_admin_level_applications.py`
- `k3l4m5n6o7p8_add_user_profile_fields.py`
- `l4m5n6o7p8q9_add_application_viewed_at.py`
- `m5n6o7p8q9r0_add_email_verifications_table.py`
- `n6o7p8q9r0s1_add_company_address.py`
- `o7p8q9r0s1t2_add_email_verification_rate_limits.py`
- `p8q9r0s1t2u3_add_application_match_scores.py`
- `q9r0s1t2u3v4_add_rbac_and_team_tables.py`
- `r0s1t2u3v4w5_seed_rbac_and_backfill_admins.py`
- `s1t2u3v4w5x6_rebackfill_b_admin_team_lead.py`
- `t2u3v4w5x6y7_seed_demo_admin_teams.py`
- `u3v4w5x6y7z8_add_admin_leave_tables.py`
- `v4w5x6y7z8a9_add_leave_change_request.py` (`admin_leave_requests.change_requested_at`/`change_request_reason`)
- `w5x6y7z8a9b0_add_audit_logs_and_reg_mod_columns.py` (`audit_logs`, `AUDIT_VIEW`, selected reg/mod columns)
- `x6y7z8a9b0c1_add_common_code_admin_and_menus.py` (head, common-code admin columns, `menus`, `CODE_MANAGE`/`MENU_MANAGE`)

Important tables:

- Auth/users: `users`, `refresh_tokens`
- RBAC/org/leave: `roles`, `permissions`, `role_permissions`, `user_roles`, `teams` (+ `users.team_id`, `users.team_role`), `admin_leave_requests`, `leave_balances`, `audit_logs`, `menus`
- Content: `categories`, `posts`
- Jobs: `job_postings`, `job_sources`, `batch_job_runs`, `common_code_groups`, `common_codes`
- Resume: `resumes`, `resume_projects`, `resume_cover_letter_sections`
- Interview: `resume_interview_sessions`, `resume_interview_questions`, `resume_interview_answers`
- Company/applications: `companies`, `applications`
- Matching: `application_match_scores`
- Email/recovery: `email_verifications`

## Main Files Changed In Current Work

Backend:

- `backend/alembic/versions/p8q9r0s1t2u3_add_application_match_scores.py`
- `backend/alembic/versions/s1t2u3v4w5x6_rebackfill_b_admin_team_lead.py`
- `backend/alembic/versions/t2u3v4w5x6y7_seed_demo_admin_teams.py`
- `backend/alembic/versions/u3v4w5x6y7z8_add_admin_leave_tables.py`
- `backend/alembic/versions/v4w5x6y7z8a9_add_leave_change_request.py`
- `backend/app/api/admin_leave.py`
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
- `backend/app/models/application_match_score.py`
- `backend/app/models/admin_leave.py`
- `backend/app/models/user.py`
- `backend/app/repositories/admin_leave_repository.py`
- `backend/app/repositories/application_repository.py`
- `backend/app/repositories/application_match_score_repository.py`
- `backend/app/repositories/company_repository.py`
- `backend/app/repositories/job_posting_repository.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/schemas/application.py`
- `backend/app/schemas/match_score.py`
- `backend/app/schemas/auth.py`
- `backend/app/schemas/company.py`
- `backend/app/schemas/admin_user.py`
- `backend/app/schemas/admin_leave.py`
- `backend/app/schemas/user.py`
- `backend/app/services/admin_leave_service.py`
- `backend/app/services/account_recovery_service.py`
- `backend/app/services/application_service.py`
- `backend/app/services/match_score_constants.py`
- `backend/app/services/match_score_service.py`
- `backend/app/services/company_provisioning_service.py`
- `backend/app/services/company_service.py`
- `backend/app/services/email_service.py`
- `backend/app/services/interview_email_service.py`
- `backend/app/services/job_posting_service.py`
- `backend/app/scripts/seed_demo_accounts.py`
- `backend/app/scripts/cleanup_demo_admins.py`
- `backend/app/scripts/generate_mock_work24_jobs.py`

Frontend:

- `frontend/src/screens/LoginPage.tsx`
- `frontend/src/screens/AccountRecoveryPage.tsx`
- `frontend/src/screens/SignupPage.tsx`
- `frontend/src/screens/user/DashboardPage.tsx`
- `frontend/src/screens/user/JobsPage.tsx`
- `frontend/src/screens/user/ApplicationsPage.tsx`
- `frontend/src/screens/user/ProfilePage.tsx`
- `frontend/src/screens/user/ResumesPage.tsx`
- `frontend/src/screens/admin/AdminUsersPage.tsx`
- `frontend/src/screens/admin/AdminJobsPage.tsx`
- `frontend/src/app/company/login/page.tsx`
- `frontend/src/app/find-account/page.tsx`
- `frontend/src/app/reset-password/page.tsx`
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
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/auth/AccountRecoveryForm.tsx`
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
- `frontend/src/styles/global.css`
- `frontend/src/stores/authStore.tsx`

Docs/context:

- `README.md`
- `frontend/README.md`
- `ai_context/API_SPEC.md`
- `ai_context/ARCHITECTURE.md`
- `HANDOFF.md`

## Verification

RBAC Phase 1 verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app` and `from app.main import app` import OK.
- `cd backend; .\.venv\Scripts\alembic.exe heads` shows a single head `r0s1t2u3v4w5`; `alembic upgrade head` applied `q9r0s1t2u3v4` (DDL) then `r0s1t2u3v4w5` (seed + backfill) cleanly.
- DB inspection confirmed the 5 new tables + `users.team_id`/`users.team_role`, the role→permission seed, and the backfill (`A → SUPER_ADMIN` ×81, `B`/`C`/`NULL → ADMIN_STAFF`; 244/244 active ADMINs have a role).
- A temporary script (created, run, then deleted) exercised the dependency: A-admin passes `LEAVE_APPROVE`/`USER_MANAGE`; C-admin passes `JOB_MANAGE` but is BLOCKED (403) on `LEAVE_APPROVE`; a plain USER is BLOCKED on all permissions. The compatibility shim grants SUPER_ADMIN permissions to an ADMIN(A) with no `user_roles` row.
- Regression: `get_current_admin_user` still allows ADMIN / blocks USER; `get_current_a_admin_user` still allows A / blocks C (ALIO collection gate intact).

RBAC + leave Phase 2 verified:

- `cd backend; .\.venv\Scripts\alembic.exe upgrade head` applied `s1t2u3v4w5x6`, `t2u3v4w5x6y7`, and `u3v4w5x6y7z8` cleanly.
- `cd backend; .\.venv\Scripts\alembic.exe heads` and `current` both show single head `u3v4w5x6y7z8`.
- DB inspection confirmed B admins have both `TEAM_LEAD` and `ADMIN_STAFF` (81 each); B permissions include `LEAVE_APPROVE`, `LEAVE_REQUEST`, `JOB_MANAGE`; C permissions include `LEAVE_REQUEST` and not `LEAVE_APPROVE`.
- DB inspection confirmed 3 demo teams, B admins as `LEAD` ×81, C admins as `MEMBER` ×81, A/null admins unassigned to team roles.
- `admin_leave_requests` and `leave_balances` tables exist; temporary verification rows were cleaned after the test (`COUNT(*) = 0` for both in the local DB after cleanup).
- API/service temporary verification covered: C cannot access pending approvals; C request routes to same-team B; B request routes to A; requester self-approval returns 403; other-team approval returns 403; insufficient balance returns 400; approval changes status to `APPROVED`; approval-after-cancel request changes `CANCEL_REQUESTED` -> `CANCELED`; A rejection of B request restores `pending_days`; existing `get_current_admin_user` and `get_current_a_admin_user` gates still pass/fail as expected.
- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `git diff --check` (line-ending warnings only)

휴가 결재 경로 통일 + 일정 변경 요청 verified (2026-06-23):

- `alembic upgrade head`로 `v4w5x6y7z8a9` 적용, 단일 head 확인. `admin_leave_requests`에 `change_requested_at`/`change_request_reason` 추가 확인.
- `from app.main import app`에서 `/admin/leave/*` 9개 라우트 등록 확인(`/admin/leave-requests/*` 잔존 0).
- 임시 검증 스크립트(생성→실행→삭제)로 실제 Postgres + TestClient(라우터/권한/서비스/리포지토리/DB 전 경로) 16/16 PASS:
  - 신청 시 pending↑·remaining↓ → 승인 시 pending→used 전환 → 반려/승인 전 취소 시 복구.
  - 잔여 초과 신청 400 차단(잔여 무변동).
  - MEMBER 신청 결재선=같은 팀 LEAD, LEAD 신청 결재선=SUPER.
  - 본인 신청 본인 승인 403(LEAVE_APPROVE 보유 LEAD도 차단), ADMIN_STAFF/OPS_ADMIN 승인 403, 타 팀 LEAD 승인 403.
  - 일정 변경 요청: PENDING→CHANGE_REQUESTED + 사유 저장 + 잔여 무변동, CHANGE_REQUESTED 직접 승인 400, resubmit으로 PENDING 복귀·잔여 재계산, 재신청 건 승인 used 전환.
  - 기존 `get_current_admin_user`/`get_current_a_admin_user` 게이트 회귀 0(ADMIN 통과·USER 차단, A 통과·C 차단).
  - 정리 후 `admin_leave_requests`/`leave_balances` COUNT 0 복원.

관리자 휴가 화면 3종 + 취소 반려 보강 verified (2026-06-23):

- 백엔드: `GET /admin/leave/balance`와 `PATCH /admin/leave/{leave_request_id}/cancel-reject` 추가. 취소 반려는 `CANCEL_REQUESTED`를 `APPROVED`로 되돌리고 잔여일은 변경하지 않는다.
- 프론트: `/admin/leave/request`, `/admin/leave/approvals`, `/admin/leave/my` 화면과 `frontend/src/api/leave.ts` 연결. 결재함의 취소 요청 건에는 "취소 승인"과 "취소 반려" 버튼을 모두 노출한다.
- 임시 검증 스크립트(생성→실행→삭제)로 실제 Postgres + TestClient 22/22 PASS:
  - `CANCEL_REQUESTED -> cancel-reject -> APPROVED`, 잔여 스냅샷 `granted=15.00`, `used=2.00`, `pending=0.00`, `remaining=13.00` 유지.
  - 본인 취소 반려, 타 팀 LEAD 취소 반려, ADMIN_STAFF/OPS_ADMIN 취소 반려는 403 차단.
  - `PENDING` 상태에서 `cancel-reject`는 400 차단.
  - 검증용 임시 사용자/팀 잔존 0건 확인.
- 확인:
  - `cd backend; .\.venv\Scripts\alembic.exe upgrade head`
  - `cd backend; .\.venv\Scripts\python.exe -m py_compile app\api\admin_leave.py app\services\admin_leave_service.py app\repositories\admin_leave_repository.py app\schemas\admin_leave.py app\models\admin_leave.py`
  - `cd backend; .\.venv\Scripts\python.exe -m compileall app`
  - `cd frontend; npm run lint`
  - `cd frontend; npm run build`

데모 관리자 조직 정리 verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app/scripts/seed_demo_accounts.py app/scripts/cleanup_demo_admins.py` 컴파일 OK; `from app.main import app` import OK(routes=70).
- 정리 전 분류: 데모 관리자 243명을 참조하는 실데이터 0건(posts/applications/companies/resumes/interview/leave/job_postings/categories 모두 0), refresh_tokens 4건만 CASCADE 대상.
- `python -m app.scripts.cleanup_demo_admins` (dry-run) → 삭제 225 / 유지 18 / 정규화 1 미리보기; `--apply`로 적용.
- 적용 후 DB 확인: 활성 ADMIN 19(A2/B3/C13/NULL1), 역할 SUPER_ADMIN 2·TEAM_LEAD 3·OPS_ADMIN 1·ADMIN_STAFF 16(데모 15+test 1), 팀별 LEAD 1/MEMBER 4, LEAVE_APPROVE=SUPER 2+TEAM_LEAD 3, orphan user_roles/refresh_tokens 0, USER/COMPANY 243/243·공고 203·지원 5 무변경, `test@test.com` 보존.
- 권한 경로(`get_user_permission_codes`) 검증: SUPER=4권한, TEAM_LEAD=LEAVE_APPROVE 보유, ADMIN_STAFF/OPS/test=LEAVE_REQUEST+JOB_MANAGE(LEAVE_APPROVE/USER_MANAGE 없음 → OPS가 SUPER로 새지 않음).
- 멱등성: cleanup 재실행 dry-run = 삭제/생성/정규화 0; `seed_demo_accounts --skip-users` 재실행 = created/normalized 0.

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

Latest account recovery rate-limit fix verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd backend; .\.venv\Scripts\alembic.exe heads`
- `cd backend; .\.venv\Scripts\alembic.exe upgrade head`
- `cd backend; .\.venv\Scripts\python.exe -c "from app.main import app; print(len(app.routes)); print([r.path for r in app.routes if 'password' in r.path or 'find-email' in r.path])"`
- `cd backend; .\.venv\Scripts\python.exe -c "from app.core.database import engine; from sqlalchemy import inspect; cols=[c['name'] for c in inspect(engine).get_columns('email_verifications')]; print('attempt_count' in cols); print('last_attempt_at' in cols)"`
- Started a temporary backend server on `127.0.0.1:8017` and verified actual HTTP behavior: repeated `POST /auth/password/reset-request` for the same email returned `200` then `429`; five wrong `POST /auth/password/reset-confirm` calls produced `EMAIL_003` and expired the active code (`attempt_count=5`, `is_used=true`). The test email row was deleted afterward.

Latest login account-recovery UI fix verified:

- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `Invoke-WebRequest http://127.0.0.1:3000/login` confirmed the personal login page contains "아이디 찾기", "비밀번호 찾기", and "Google로 계속하기".
- `Invoke-WebRequest http://127.0.0.1:3000/company/login` confirmed the company login page contains "아이디 찾기" and "비밀번호 찾기" and does not render "Google로 계속하기".
- In-app Browser verification was attempted but the Browser runtime failed in this Windows sandbox (`spawn setup refresh`).

Latest account-recovery route/template/button/masking work verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `git diff --check` (line-ending warnings only)
- In-app Browser opened `http://127.0.0.1:3000/company/dashboard` against the running Next dev server and found no console errors, but without an authenticated company session it stayed on the auth/loading state, so the score UI was not visually verified in-browser.
- Started the Next dev server at `http://127.0.0.1:3000`. Chrome headless screenshots verified `/login`, `/find-account`, `/find-account?audience=company`, `/reset-password`, and `/reset-password?audience=company`.
- Chrome DevTools Protocol verified the `/login` "아이디 찾기" link navigates to `/find-account`; the login button hover changed background color and active state changed brightness; account-recovery text links show pointer cursor, underline, and brightness hover feedback.
- Temporary backend servers verified `POST /auth/find-email`: no-match returns `200` without `masked_email`; matching personal USER returns `200` with a masked email. SMTP sending was attempted in the sandbox and failed with `PermissionError`; an escalation to send through Gmail SMTP was rejected as private-data export to an unverified external destination, so inbox rendering was not verified in this run.
- Email template structure was checked with sample values: account-recovery HTML contains table-based markup, no `<style>`, no `display:flex`, and no `display:grid`; plain-text alternatives are still provided through `EmailMessage.set_content`.

Latest application status-management phase verified:

- Local DB status count before changes: `CANCELED=1`, `SUBMITTED=2`, `VIEWED=1`, `ACCEPTED=0`; no `ACCEPTED` data conversion was needed.
- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd backend; .\.venv\Scripts\python.exe -c "from app.main import app; print([r.path for r in app.routes if 'applications' in r.path])"` confirmed `PATCH /company/applications/{application_id}/status` is registered.
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- Temporary FastAPI `TestClient` data verified: `COMPANY` cannot `POST /applications` (403), owning company can mark an application `REJECTED` (200), manual `INTERVIEW` status is rejected by the request whitelist (422), and a different company cannot update the application (404). Temporary rows were cleaned afterward.

All blocking checks passed. `git diff --check` only prints line-ending warnings in this workspace.

Latest company account-recovery API/UI work verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `cd backend; .\.venv\Scripts\python.exe -c "from app.main import app; print([r.path for r in app.routes if 'find-email' in r.path or 'password/reset' in r.path])"` confirmed `/auth/company/find-email` and `/auth/company/password/reset-request` are registered.
- FastAPI `TestClient` with a temporary COMPANY user/company row verified `POST /auth/company/find-email` returns `200` with `masked_email`, and `POST /auth/company/password/reset-request` returns `200`. SMTP is blocked in the sandbox, so the send attempts logged masked-recipient failures but the API behavior was verified.
- FastAPI `TestClient` verified `POST /auth/password/reset-request` still returns `200` then `429` for immediate repeat sends. Two immediate wrong `POST /auth/password/reset-confirm` requests returned `400`/`400` (not `429`), and five wrong attempts expired the code (`attempt_count=5`, `is_used=true`).
- `Invoke-WebRequest` against the running Next dev server at `http://127.0.0.1:3000` confirmed `/find-account?audience=company`, `/reset-password?audience=company`, and `/find-account` render the expected recovery form text. In-app Browser failed with the Windows sandbox `spawn setup refresh` issue; Chrome headless also exited before producing a screenshot in this environment.

Latest interview-email UI/status flow verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `git diff --check` (line-ending warnings only)
- FastAPI `TestClient` with temporary company/applicant/job/resume/application rows monkeypatched the interview email sender to avoid real SMTP. It verified successful `POST /company/applications/{application_id}/interview-email` returns `200` and changes DB status to `INTERVIEW`; a past `interview_at` returns `422` without changing status; a different company receives `404` for the same application. Temporary rows were cleaned afterward.

Latest application matching score work verified:

- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd backend; .\.venv\Scripts\alembic.exe heads` confirmed `p8q9r0s1t2u3` is the head.
- `cd backend; .\.venv\Scripts\alembic.exe upgrade head`
- `cd backend; .\.venv\Scripts\python.exe -c "from app.core.database import engine; from sqlalchemy import inspect; print([c['name'] for c in inspect(engine).get_columns('application_match_scores')])"` confirmed the score table columns.
- Service-level temporary data test created a USER, resume, manual job, application, and stored match score; the response included score/grade/matched skills, and temporary rows were cleaned afterward.
- Hardening check confirmed `local-match-v1` is deterministic keyword/text scoring without embeddings, LangChain, or LLM calls; empty resume/job inputs avoid division by zero; scores stay clamped to 0-100; `ApplicationMatchScoreResponse` does not expose internal evidence JSON; sensitive demographic-only text similarity returns 0; and local `.env` files are ignored rather than tracked.
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `git diff --check` (line-ending warnings only)

Latest repository status / AI-trace audit / docs sync verified:

- `git status --short --untracked-files=all` showed no tracked changes before this audit, aside from Git's user-level ignore permission warning in this Windows sandbox.
- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` were compared and are still identical.
- UTF-8 reads and fixed-string searches found no committed mojibake/replacement-character Korean corruption; the earlier garbled Korean display was PowerShell default encoding, not file content.
- Searches found no committed `as an AI`, `AI-generated`, `Generated by`, `ChatGPT`, `Claude`, `Gemini`, or lorem-ipsum markers.
- Docs were brought back in sync with implemented company job management, account recovery, application cancellation, company application status/interview-email APIs, match-score response notes, and the current resume upload policy.
- `.tmp-*.png` screenshot artifacts exist at the repository root as local verification leftovers; they are not reported by `git status` and were left untouched.
- Checks after the docs sync:
  - `cd backend; .\.venv\Scripts\python.exe -m compileall app`
  - `cd backend; .\.venv\Scripts\alembic.exe heads`
  - `cd frontend; npm run lint`
  - `cd frontend; npm run build`
  - `git diff --check`

Latest admin audit columns / audit logs work verified:

- Added `RegModAuditMixin` and request audit context for `reg_user_id`, `reg_ip`, `reg_dt`, `mod_user_id`, `mod_ip`, and `mod_dt`; attached it only to `user_roles`, `leave_balances`, and `admin_leave_requests`.
- Added `audit_logs`, `AUDIT_VIEW`, `GET /admin/audit-logs`, and an admin audit log screen at `/admin/audit-logs`.
- `user_roles` ORM inserts/deletes now write audit log rows; admin leave status transitions write before/after audit data without request reasons or password fields.
- `cd backend; .\.venv\Scripts\alembic.exe upgrade head` and `current` confirmed `w5x6y7z8a9b0`.
- Temporary FastAPI `TestClient` verification against real local PostgreSQL passed: X-Forwarded-For was captured, reg/mod columns were populated, role grant audit log was written with role code, leave approval audit log had `PENDING -> APPROVED`, `AUDIT_VIEW` missing user got 403, SUPER_ADMIN got filtered audit-log results, and temporary rows were cleaned (`tmp.audit.*` users/teams = 0).
- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `git diff --check` (line-ending warnings only)

Latest admin common-code / dynamic-menu work verified:

- Extended the existing ALIO common-code tables instead of replacing them: `common_code_groups` and `common_codes` now include `RegModAuditMixin` columns plus admin-facing `sort_order`, `use_yn`, and item `attr1`/`attr2`.
- Added `CODE_MANAGE`, `MENU_MANAGE`, `/admin/common-codes/*`, `/admin/menus/*`, and self-referencing `menus` with `required_permission` filtering. SUPER_ADMIN receives both new permissions in migration seed.
- Admin sidebar keeps the fixed `adminNav` list and appends DB-driven menu tree results from `GET /admin/menus/tree`; new screens are `/admin/common-codes` and `/admin/menus`.
- Common-code and menu create/update/delete paths write `audit_logs` rows with focused before/after data and no password fields.
- `cd backend; .\.venv\Scripts\python.exe -m alembic upgrade head` and `current` confirmed `x6y7z8a9b0c1`.
- Temporary FastAPI `TestClient` verification against real local PostgreSQL passed: CODE/MENU manage missing user got 403, authenticated code read worked, group/item create-update-disable worked, duplicate `(group_code, code)` returned 409, reg/mod columns captured `X-Forwarded-For`, parent-child menu tree was correct, cycle update returned 400, permission-filtered tree hid a `CODE_MANAGE` child from an ADMIN_STAFF user, audit-log API returned menu audit rows, and temporary users/groups/menus were cleaned to 0 rows.
- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

Latest final security/error audit verified:

- Public `GET /jobs/{job_id}` now returns 404 for `status='HIDDEN'`, matching list behavior and preventing direct-id access to hidden company postings.
- Request validation error responses no longer include raw `input` values, so malformed password/code/token-like fields are not echoed in API 422 bodies.
- Security sweep checked route dependency gates, ownership checks on user/company data, raw SQL usage, secret patterns (`sk-`, `AIza`, API key names), token/password/code logging, and RBAC shim paths.
- Alembic `heads` and `current` confirmed single head `x6y7z8a9b0c1`.
- Temporary FastAPI `TestClient` verification passed: validation error details omit input values and direct hidden job detail returns 404; temporary hidden job row was deleted.
- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

User role grant/revoke (RBAC management) added on top of existing `user_roles`:

- New endpoints on `admin_users` router, all gated by `require_permission("USER_MANAGE")`:
  - `GET /admin/users/{user_id}/roles` — assigned role codes + every assignable active role with its permission list + `super_admin_count`.
  - `POST /admin/users/{user_id}/roles` body `{role_code}` — assign; duplicate assignment returns 409 `ROLE_002`.
  - `DELETE /admin/users/{user_id}/roles/{role_code}` — revoke.
- Safety guards in `RbacService`: self `SUPER_ADMIN` revoke blocked (403 `ROLE_004`), last `SUPER_ADMIN` revoke blocked (409 `ROLE_005`).
- `RbacRepository` gained write methods (`assign_role`/`revoke_role`) plus role/permission/count reads; no new RBAC tables. Grant/revoke audit rows are written automatically by the existing `UserRole` ORM event listener (actor/role_code/before·after, no sensitive fields).
- Added missing `ErrorCode.USER_NOT_FOUND` (`USER_001`); it was referenced in `admin_users.get_user_detail` but undefined, which would have raised `AttributeError` on a missing-user lookup.
- Frontend: `/admin/users/roles` screen (search → user list → role detail with per-role permission chips, assign/revoke buttons, emphasized `SUPER_ADMIN` confirm dialog, guard-disabled buttons with reason text, success toast + refetch), `userRoles` API client, and a `역할 관리` adminNav item.
- Temporary `TestClient` + DB verification passed 17/17: non-`USER_MANAGE` user 403 / `SUPER_ADMIN` 200, assign reflects in `user_roles` and permission set (`JOB_MANAGE` gained), duplicate assign 409, revoke reflects, self-`SUPER_ADMIN` revoke blocked, last-`SUPER_ADMIN` revoke blocked (isolated rolled-back tx), audit `CREATE`/`DELETE` rows carry `role_code`/actor with no sensitive data; all temporary users/roles/audit rows cleaned to 0.
- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

Admin screen permission/loading fix + demo login accounts:

- Diagnosis: the `/admin/users/roles`, audit-log, and dynamic-menu screens all failed for `test@test.com` because it only held `ADMIN_STAFF` (perms `{JOB_MANAGE, LEAVE_REQUEST}`), so it lacked `USER_MANAGE` (roles 403), `AUDIT_VIEW` (audit 403), and `MENU_MANAGE`/`CODE_MANAGE` (dynamic menus `메뉴 관리`/`공통코드 관리` hidden). No endpoint/path bug — pure permission shortfall.
- `seed_demo_accounts.py` gained `seed_login_test_accounts` + `--login-test` / `--only-login-test` flags (idempotent). It normalizes the local `@test.com` login accounts: `test@test.com` → admin_level A + `SUPER_ADMIN` (password preserved), `testb` → B + `TEAM_LEAD`, `testc` → C + `ADMIN_STAFF`, `testd` → C + `OPS_ADMIN`. `testb/testc/testd` use demo-only common password `12341234` (hashed, never logged); run `python -m app.scripts.seed_demo_accounts --only-login-test` to apply.
- `/admin/users/roles` search now filters to `role=ADMIN` (RBAC roles target admins/staff, so COMPANY/USER no longer clutter the assignment list).
- Verified with `TestClient` (minted token for `test@test.com`): role list 200 + ADMIN-only, role detail 200, audit-logs 200, menu tree exposes `/admin/common-codes` + `/admin/menus`; regression — `testc` (ADMIN_STAFF) still 403 on roles/audit and dynamic menus stay hidden (least privilege intact). 7/7 passed.
- `cd backend; .\.venv\Scripts\python.exe -m compileall app`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

pgvector 도입 v2.0 STEP 1 완료:

- 현재 브랜치가 `main`이라 작업 브랜치 `feat/pgvector-v2-step1`을 만들어 진행했다.
- `docker-compose.yml`의 PostgreSQL 이미지를 `postgres:16-alpine`에서 `pgvector/pgvector:pg16`으로 교체했다. 기존 named volume `jobfit_postgres_data`는 그대로 유지했고, `down -v`나 볼륨 삭제는 사용하지 않았다.
- `backend/requirements.txt`에 `pgvector==0.4.2`를 추가했다. 로컬 venv 설치 확인 결과 `pgvector 0.4.2`와 런타임 의존성 `numpy 2.5.0`이 설치됐고 `pip check`는 정상이다.
- 신규 Alembic migration `y7z8a9b0c1d2_enable_pgvector_extension.py`를 추가했다. `upgrade()`는 `CREATE EXTENSION IF NOT EXISTS vector`, `downgrade()`는 `DROP EXTENSION IF EXISTS vector`만 수행한다. 이번 단계에서는 벡터 컬럼과 임베딩 테이블을 만들지 않았다.
- 교체 전 기준: table_count 29, users 564, roles 4, user_roles 25, admin_leave_requests 0, applications 5.
- 이미지 교체 후, migration 전 기준도 같은 count였고 `vector` extension은 0건이었다.
- 최종 검증: Alembic head/current `y7z8a9b0c1d2`, `pg_extension`의 `vector` extversion `0.8.3`, `SELECT '[1,2,3]'::vector` 결과 `[1,2,3]`.
- Downgrade/upgrade 검증 완료: `alembic downgrade -1` 후 current `x6y7z8a9b0c1`, extension 0건 확인, 다시 `alembic upgrade head`로 최종 head 복구.
- 최종 row count는 table_count 29, users 564, roles 4, user_roles 25, admin_leave_requests 0, applications 5로 교체 전과 동일하다.
- 검증:
  - `docker compose up -d postgres`
  - `docker compose ps postgres`
  - `cd backend; .\.venv\Scripts\python.exe -m pip install pgvector==0.4.2`
  - `cd backend; .\.venv\Scripts\python.exe -m pip check`
  - `cd backend; .\.venv\Scripts\alembic.exe upgrade head`
  - `cd backend; .\.venv\Scripts\alembic.exe downgrade -1`
  - `cd backend; .\.venv\Scripts\alembic.exe upgrade head`
  - `cd backend; .\.venv\Scripts\alembic.exe heads`
  - `cd backend; .\.venv\Scripts\alembic.exe current`
  - `cd backend; .\.venv\Scripts\python.exe -m compileall app`
  - `cd backend; .\.venv\Scripts\python.exe -c "from pgvector.sqlalchemy import Vector; from app.main import app; print(Vector(3)); print(len(app.routes)); print(any(route.path == '/admin/menus/tree' for route in app.routes)); print(any(route.path == '/admin/leave/pending' for route in app.routes))"`
  - `git diff --check` (line-ending warnings only)

RAG v2 STEP 2 이력서 청킹 + 임베딩 저장 완료:

- STEP1 브랜치에서 `feat/rag-resume-chunks-v2-step2` 브랜치를 만들어 진행했다.
- 신규 모델 `ResumeChunk`를 추가했다. 테이블은 `resume_chunks`, PK는 `id`, `resume_id`는 `resumes.resume_id`를 `ON DELETE CASCADE`로 참조하며, `embedding`은 `Vector(1536)`이다. `AuditMixin`과 `RegModAuditMixin`을 함께 적용했다.
- 신규 migration `z8a9b0c1d2e3_create_resume_chunks.py`를 추가했다. `resume_chunks` 생성 후 `ix_resume_chunks_embedding_hnsw` HNSW 인덱스를 `vector_cosine_ops`로 만든다. 공고 chunk 테이블은 만들지 않았다.
- `app/services/rag/chunking.py`: `split_resume_into_chunks(resume)`가 `parsed_data`, `resume_projects`, `resume_cover_letter_sections`를 섹션별 텍스트로 모으고, 500자를 넘는 섹션은 문단과 문장 경계를 우선해 나눈다. 인접 chunk에는 약 10%인 50자 overlap을 둔다.
- `app/services/rag/embedding.py`: `embed_texts(texts)`는 `settings.openai_api_key`를 사용해 `text-embedding-3-small`로 한 번에 배치 임베딩을 요청한다. `dimensions` 파라미터는 보내지 않고, 응답 벡터가 1536차원인지 검증한다.
- `app/services/rag/resume_chunk_service.py`: `rebuild_resume_chunks(db, resume_id, ...)`는 같은 `resume_id`의 기존 chunk를 전부 삭제하고, 새 chunk와 embedding을 삽입한 뒤 `{"resume_id", "total", "by_section"}`를 반환한다. 임베딩 또는 DB 실패 시 rollback한다.
- 신규 endpoint는 기존 라우터 컨벤션에 맞춰 `POST /resumes/{resume_id}/chunks/rebuild`로 등록했다. `/api/v1` prefix는 현재 앱에 없어서 추가하지 않았다. 본인 이력서 또는 `ADMIN`만 허용한다.
- 실제 DB 검증:
  - `resume_id=35` 소유자 토큰으로 rebuild 호출 1회차 200, 20 chunks 생성.
  - 같은 이력서 rebuild 2회차도 200, 20 chunks로 동일해 중복이 없음을 확인.
  - 섹션별 결과: 기본정보 1, 기술스택 1, 학력 1, 교육 1, 경력 1, 자격증 1, 프로젝트 5, 자소서 9.
  - `vector_dims(embedding)` 결과 1536.
  - `ORDER BY embedding <=> (SELECT embedding FROM resume_chunks ... LIMIT 1) LIMIT 5` 정상 동작.
  - 검증용 `resume_id=35` chunk는 삭제했고 최종 `resume_chunks` row 수는 0이다.
  - 일반 비소유자 `USER` 토큰으로 같은 rebuild 호출 시 404 `RESUME_001` 확인.
- Migration 검증:
  - `cd backend; .\.venv\Scripts\python.exe -m alembic upgrade head`
  - `cd backend; .\.venv\Scripts\python.exe -m alembic downgrade -1`
  - `cd backend; .\.venv\Scripts\python.exe -m alembic upgrade head`
  - 최종 head/current `z8a9b0c1d2e3`, HNSW 인덱스 존재, `resume_chunks=0`.
- 정적 검증:
  - `cd backend; .\.venv\Scripts\python.exe -m compileall app`
  - `cd backend; .\.venv\Scripts\python.exe -m alembic heads`
  - `git diff --check` (line-ending warnings only)
- 주의: 이 작업부터 Alembic 실행은 `.\.venv\Scripts\python.exe -m alembic ...` 형태로 검증했다. 이 환경의 `alembic.exe` 런처는 오래된 경로를 참조해 신규 `pgvector` 패키지를 찾지 못할 수 있다.

RAG v2 STEP 3 공고 요구 기반 이력서 chunk 검색 진행:

- `feat/rag-retrieval-v2-step3` 분기에서 진행 중이다.
- STEP3 전 점검 결과, STEP2의 `rebuild_resume_chunks`는 기존 chunk 삭제 뒤 OpenAI 임베딩을 호출하고 있었다. 삭제와 삽입은 한 트랜잭션이었지만 네트워크 호출 중 트랜잭션을 점유하고, 임베딩 실패 때 기존 chunk 보존 요구를 만족하지 못했다.
- 이를 먼저 별도 커밋 `1b343ed fix(rag): rebuild를 임베딩 후 원자적 교체로 변경`으로 고쳤다. 새 순서는 chunk 분리와 임베딩을 먼저 끝낸 뒤, 기존 chunk 삭제와 새 chunk 삽입만 한 트랜잭션으로 묶는다.
- `app/services/rag/retrieval.py`를 추가했다. `build_job_query_text(job_posting)`는 `parsed_skills`, 제목, 경력, 학력, 고용 형태, NCS, `raw_content`의 요구 관련 줄을 검색 쿼리로 합친다. `retrieve_resume_chunks(...)`는 `embed_texts([query_text])`로 쿼리 임베딩을 만들고 `resume_chunks.embedding <=> :qvec` 코사인 거리순으로 같은 `resume_id` chunk만 반환한다. 지금 단계는 단일 이력서 안의 작은 검색이라 HNSW 강제나 튜닝은 하지 않는다.
- `app/schemas/rag.py`를 추가했다. 요청은 `{job_posting_id, query_text, top_k, sections}`이며 공고 ID나 직접 쿼리 중 하나가 필요하다. 응답은 `{resume_id, query_preview, top_k, results}`이고 결과에는 `chunk_id`, `section`, `content`, `distance`, `similarity`가 들어간다.
- `POST /resumes/{resume_id}/retrieve`를 기존 이력서 라우터에 추가했다. `/api/v1` prefix는 현재 앱 컨벤션에 없어서 붙이지 않았다. 권한은 기존 rebuild와 같이 본인 또는 `ADMIN`만 허용하며, 비소유자는 `404 RESUME_001` 흐름을 따른다.
- `job_posting_id`가 있으면 `JobPostingRepository.get_by_id()`로 공고를 읽고, 없으면 `query_text`를 사용한다. 둘 다 없거나 공고 기반 쿼리가 비면 422를 반환한다. 없는 공고는 `404 JOB_001`, 임베딩 설정 없음은 503, 임베딩 실패는 `502 RESUME_008`이다.
- 로컬 검증:
  - `cd backend; .\.venv\Scripts\python.exe -m compileall app`
  - 새로 건드린 `backend/app/api/resumes.py`, `backend/app/schemas/rag.py`, `backend/app/services/rag/retrieval.py` 범위에서 한자 코드포인트 없음 확인.
  - 더미 설정으로 SQLAlchemy PostgreSQL dialect 컴파일을 확인했고, 검색 정렬식이 `resume_chunks.embedding <=> %(embedding_1)s AS distance`로 생성됨을 확인했다.
- (해소됨) 이전엔 실제 Postgres + OpenAI를 쓰는 `resume_id=35` rebuild/retrieve 검증이 사용량 제한으로 미완이었으나, 아래 "RAG v2 STEP 1~3 실DB+OpenAI end-to-end 검증" 절에서 17/17 PASS로 닫았다. STEP3 코드는 이미 `a7e63ba`로 커밋되어 있다.

RAG v2 STEP 1~3 실DB+OpenAI end-to-end 검증 완료 (2026-06-25):

- 목적: 코드(`552251b`/`c2ba92c`/`a7e63ba`, 브랜치 `feat/rag-retrieval-v2-step3`)가 실제로 도는지 닫는 검증. 새 기능 추가 없음. 검증 결과 코드 결함 0건이라 코드 보정도 없음.
- STEP A(환경/무손상): `docker-compose up -d`로 `pgvector/pgvector:pg16` healthy. 단일 head/current `z8a9b0c1d2e3`. `pg_extension` `vector` 0.8.3 활성, `SELECT '[1,2,3]'::vector` 정상. 기존 데이터 무손상: users 564, user_roles 25, applications 5, job_postings 203, resumes 34 (admin_leave_requests 0은 데모 검증 정리 후 정상 베이스라인).
- STEP B(청킹+임베딩, `POST /resumes/35/chunks/rebuild`, 실제 OpenAI `text-embedding-3-small`):
  - 1회차 200, total 20. 섹션별: 기본정보 1·기술스택 1·학력 1·교육 1·경력 1·자격증 1·프로젝트 5·자소서 9.
  - `vector_dims(embedding)` 전부 1536, embedding NULL 0건. 응답 total == DB count(20).
  - 멱등: 2회차도 200·total 20·섹션 분포 동일(삭제 후 원자적 재삽입이라 중복 0).
- STEP C(검색, `POST /resumes/35/retrieve`, 실제 OpenAI 쿼리 임베딩):
  - 직접 쿼리("백엔드 개발자 채용. Java, Spring Boot, REST API, JPA, MySQL, ..."): distance 오름차순 [0.4139, 0.4341, 0.4879, 0.4918, 0.5091], 1위가 기술스택 chunk(Java/SpringBoot/JPA/QueryDSL/RESTAPI...), 이어 Back-End 자소서·프로젝트 chunk. `similarity == 1 - distance` 일치. 의미 검색 정상.
  - 공고 기반(`job_posting_id=92`, "신입 백엔드 개발자 (Java/Spring Boot)"): 200, 1위 동일하게 기술스택 chunk. `build_job_query_text` 경로 정상.
  - `sections=["기술스택"]` 필터: 해당 섹션만 반환.
- HNSW/EXPLAIN: `ix_resume_chunks_embedding_hnsw`(`hnsw (embedding vector_cosine_ops)`) 존재. 실제 retrieve는 `WHERE resume_id=:r` + cosine `ORDER BY ... LIMIT`이라 ~36행 대상 Seq Scan + Sort로 계획된다(소량 단일 이력서 스코프에서 정상·최적). 같은 정렬식을 필터 없이 `enable_seqscan=off`로 돌리면 `Index Scan using ix_resume_chunks_embedding_hnsw`로 HNSW를 사용함을 확인 → 인덱스 자체는 유효. 즉 per-resume 필터에서 HNSW 미사용은 버그가 아니라 의도된 계획이다. (전 이력서 글로벌 ANN이 필요해질 때 별도 전략 고려.)
- 검증 방식: 실제 Postgres + FastAPI `TestClient`(라우터→권한→service→repository→DB→OpenAI 전 경로). `get_current_user`만 resume_id=35 소유자(user 794)로 오버라이드. 임시 스크립트는 저장소 밖 scratchpad에서 실행, DB에 임시 사용자/공고/휴가행 생성 없음.
- 데이터 상태: resume_id=35의 20개 chunk는 STEP 4(retrieve 소비)에서 바로 쓰일 정상 데이터라 유지한다. (STEP2 절의 "resume_chunks=0"은 이 검증으로 갱신된 옛 기록이며, 필요 시 `POST /resumes/{id}/chunks/rebuild`로 언제든 재생성 가능.)
- 다음: STEP 4(LangChain — 공고+이력서 교차 맞춤 질문)로 진입 가능. retrieve가 입력 컨텍스트로 검증되어 안전하다.

RAG v2 STEP 4 자동 청킹 + 공고 맞춤 면접질문 완료 (2026-06-25):

- 작업 브랜치: `feat/rag-job-interview-v2-step4`.
- 자동 청킹:
  - `POST /resumes` 업로드 성공 뒤 `BackgroundTasks`로 `rebuild_resume_chunks_background()`를 예약한다. 업로드 응답은 막지 않고, 실패해도 로그만 남기며 기존 수동 `POST /resumes/{id}/chunks/rebuild`는 유지한다.
  - 관리자 이력서 갱신 `PATCH /admin/users/resumes/{resume_id}` 뒤에도 같은 background rebuild를 예약한다.
  - `rebuild_resume_chunks(..., skip_if_unchanged=True)`를 추가했다. 현재 split 결과의 `(section, chunk_index, content)`가 기존 `resume_chunks`와 같으면 OpenAI 임베딩 호출 없이 `skipped=True`로 반환한다. 내용이 바뀌면 기존 chunk 삭제 후 재삽입 흐름은 기존 STEP2 로직을 재사용한다.
- 공고 맞춤 질문:
  - 신규 endpoint: `POST /resumes/{resume_id}/interview-questions/job-based`, body `{ "job_id": number | null }`.
  - 권한은 기존 `ResumeService.get_resume(resume_id, user_id)`로 본인 이력서만 허용한다. 타인 이력서는 404로 차단된다.
  - `job_id`가 없으면 해당 이력서로 지원한 최신 활성 application의 공고를 사용한다. `job_id`가 있으면 지정 공고를 사용하며, 숨김 공고는 본인 활성 application이 있을 때만 허용한다.
  - 생성 전 `rebuild_resume_chunks(..., skip_if_unchanged=True)`를 한 번 보장 호출해 background가 늦어도 최신 chunk를 사용한다. unchanged면 임베딩 비용 없이 스킵된다.
  - `build_job_query_text(job)` + `retrieve_resume_chunks(top_k=7)` 결과를 LangChain `PromptTemplate | ChatOpenAI | PydanticOutputParser` 체인에 넣어 1회 LLM 호출로 질문 5개를 만든다.
  - 응답은 `{ resume_id, job_id, job_title, company_name, model, chunk_count, questions: [{ question, based_on_resume, related_to_job }] }`.
  - 신규 의존성: `langchain==1.3.11`, `langchain-openai==1.3.3`; `pip check` 통과. LangChain 의존성 때문에 `websockets`는 `15.0.1`로 핀 조정했다.
- 프론트:
  - `/user/resumes`의 기존 v1 "면접 연습" 패널은 그대로 두고, 별도 "공고 맞춤 면접질문" 패널을 추가했다.
  - `GET /applications/me` 결과 중 현재 이력서의 비취소 지원 공고만 선택지로 보여준다. 기본값은 최신 지원 공고다.
  - 생성 결과는 사용자 화면에서 질문만 표시한다. 응답에는 개발 검증용 `model`, `chunk_count`, `based_on_resume`, `related_to_job`가 남아 있지만 `/user/resumes`에는 모델명, chunk 수, 이력서 근거, 공고 연결점을 노출하지 않는다.
  - 프롬프트는 실제 면접 흐름처럼 1번 소개형 워밍업, 2번 직무 기초, 3~4번 경험 기반, 5번 심화 질문 순서로 생성하도록 조정했다.
- 실제 검증:
  - Alembic head/current `z8a9b0c1d2e3`.
  - Docker 상태 조회는 로컬 Docker 권한 문제로 실패했지만, Alembic과 TestClient 검증은 실제 PostgreSQL에 연결해 통과했다.
  - 임시 PDF 업로드로 수동 rebuild 없이 자동 chunk 3개 생성 확인.
  - 같은 임시 이력서에 `rebuild_resume_chunks(skip_if_unchanged=True)` 재호출 시 `skipped=True`, chunk count 유지 확인.
  - 관리자 갱신 endpoint로 raw/parsed/project 내용을 바꾼 뒤 자동 chunk 6개로 갱신되고 새 내용(`Updated Spring Boot JWT`) 반영 확인.
  - `resume_id=35`, `job_id=92`로 job-based endpoint 실제 OpenAI 호출 200, 질문 5개, retrieve chunk 7개 사용. 현재 DB의 resume 35에는 `JWT`, `Spring`, `Java` 근거가 있고 `JobFolio` 문자열은 없음(요청 문맥과 달리 현재 데이터 기준).
  - 타인 이력서로 같은 endpoint 호출 시 404 차단 확인.
  - 기존 v1 면접질문 endpoint는 임시 세션 생성 방식으로 201, 질문 5개 확인 후 세션 삭제.
  - 임시 검증 user/resume/chunk/file 모두 정리: `codex_step4_users=0`, `debug_step4_users=0`, `codex_step4_resumes=0`; `resume_id=35` chunk 20개 유지.
  - UX 개선 후 `resume_id=35`, `job_id=213` 실제 OpenAI 호출 200. 질문 순서: 1번 프로젝트/업무 소개, 2번 Spring REST 계층 기초, 3번 JPA/QueryDSL 선택 경험, 4번 JWT 인증 구현 경험, 5번 MySQL/AWS 성능·확장성 심화. 기존 v1 면접질문 endpoint도 201, 질문 5개 확인 후 세션 삭제.
  - `/user/resumes` 렌더 코드에서 job-based 결과의 `model`, `chunk_count`, `based_on_resume`, `related_to_job` 표시를 제거했다. `frontend/src/api/types.ts`에는 API 호환을 위해 필드를 유지한다.
- 정적 검증:
  - `cd backend; .\.venv\Scripts\python.exe -m pip check`
  - `cd backend; .\.venv\Scripts\python.exe -m compileall app`
  - `cd frontend; npm run lint`
  - `cd frontend; npm run build`
  - `git diff --check` (line-ending warnings only)

## Known Remaining Work

- Account recovery UI now lives on `/find-account` and `/reset-password`, with personal and company find-email/password-reset wired. Interview-email sending is wired from the company resume modal. A real send still requires valid Gmail app-password credentials in `.env` (and `GOOGLE_MAPS_API_KEY` for the interview map; without it the email sends with the Maps link but no inline map image). Inbox rendering for the recovery/interview templates still needs a user-approved real recipient/send test outside sandbox restrictions.
- Add cleanup/retention for expired `email_verifications` rows, especially dummy rows from non-existing account recovery requests.
- Signup email-verification (JobFolio `/api/join/send-email-verification` + `/verify-email-token`) is still not implemented; it can reuse the `email_verifications` table with `purpose='SIGNUP'`.
- Company self-signup and broader company layout beyond the current dashboard/jobs screens are not implemented.
- Full admin A/B/C account-management actions are not implemented.
- `frontend/src/screens/user/MatchesPage.tsx` still uses old mock matching stats; application-level company-side stored match scores are implemented separately.
- Vector embedding/semantic matching with sentence-transformers + pgvector is still planned but not implemented; current application match scoring is deterministic `local-match-v1` and does not add new dependencies.
- Work24 public API integration remains constrained by API approval; mock and ALIO flows are available for demo/development.
