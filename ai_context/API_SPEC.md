# API_SPEC

Do not include secrets, API keys, tokens, or `.env` values in this document.

## Common

Error response shape:

```json
{ "code": "AUTH_001", "message": "...", "details": [] }
```

Important error code groups:

- Common/auth: `COMMON_*`, `AUTH_*`
- Categories/posts: `CATEGORY_*`, `POST_*`
- Jobs/collection: `JOB_*`, `JOB_SOURCE_*`, `BATCH_*`, `CODE_*`
- Resumes/interview: `RESUME_*`, `OPENAI_API_KEY_MISSING`, `INTERVIEW_*`
- Applications/company: `APPLICATION_001`, `COMPANY_001`
- Admin leave: `LEAVE_*`

## Auth `/auth`

| Method | Path | Description |
|---|---|---|
| POST | `/auth/signup` | Create user, issue access token, set refresh cookie |
| POST | `/auth/login` | Login by email, or company business number when identifier is 10 digits |
| POST | `/auth/refresh` | Rotate/validate refresh token and issue new access token |
| POST | `/auth/logout` | Revoke refresh token and clear cookie |
| GET | `/auth/me` | Current user |
| PATCH | `/auth/me` | Update name/password/profile fields |
| DELETE | `/auth/me` | Soft-delete current account |
| POST | `/auth/find-email` | Personal account email lookup by name and phone |
| POST | `/auth/company/find-email` | Company account email lookup by manager/representative name and business number |
| POST | `/auth/password/reset-request` | Request personal password reset code |
| POST | `/auth/company/password/reset-request` | Request company password reset code |
| POST | `/auth/password/reset-confirm` | Verify reset code, send temporary password, and revoke refresh tokens |

`UserResponse` includes `role`, `admin_level`, and optional profile fields.

## Categories And Posts

Categories:

- `GET /categories`: public active categories only
- `GET /admin/categories`: admin list including inactive categories
- `POST /categories`: ADMIN
- `GET /categories/{category_id}`
- `PATCH /categories/{category_id}`: ADMIN
- `DELETE /categories/{category_id}`: ADMIN

Posts:

- `GET /posts?offset&limit&category_id`
- `POST /posts`: ADMIN
- `GET /posts/{post_id}`
- `PATCH /posts/{post_id}`: ADMIN
- `DELETE /posts/{post_id}`: ADMIN

## Jobs

User-facing:

- `GET /jobs`
- `GET /jobs/filter-options`
- `GET /jobs/{job_id}`

`GET /jobs` supports:

- Pagination: `page`, `size`
- Source/status filters: `source`, `data_source`, `status`
- Code filters: `location_code`, `employment_type_code`, `education_code`, `career_level_code`
- Text filters: `keyword`, `region`, `education`, `employment_type`, `ncs_category`

Admin collection:

- `POST /admin/job-sources/alio/collect`: A-level ADMIN only
- `POST /admin/jobs/sources/work24/collect`: ADMIN, currently records BLOCKED while approval is pending
- `POST /admin/jobs/sources/mock/load`: ADMIN

`job_postings.data_source`: `PRODUCTION`, `MOCK`, `MANUAL`.

## Applications

| Method | Path | Description |
|---|---|---|
| POST | `/applications` | Current user sends a selected resume to a selected job |
| GET | `/applications/me` | Current user's application history |
| DELETE | `/applications/{application_id}` | Cancel current user's own application |

Create request:

```json
{ "job_id": 1, "resume_id": 10 }
```

Duplicate active applications for the same `(user_id, job_id)` return `APPLICATION_001`.
Canceling an application changes its status to `CANCELED`, marks it inactive for duplicate checks, and keeps it in the user's application history.

## Company

| Method | Path | Description |
|---|---|---|
| GET | `/company/dashboard` | COMPANY-only dashboard with counts, received applicants, and match-score summaries |
| GET | `/company/applications/{application_id}/resume` | View applicant resume metadata/parsed summary and mark first view as `VIEWED` |
| GET | `/company/applications/{application_id}/resume/file` | Preview or download the original resume file |
| PATCH | `/company/applications/{application_id}/status` | Mark a company-owned application `REJECTED` |
| POST | `/company/applications/{application_id}/interview-email` | Send interview invitation email and set status to `INTERVIEW` after successful send |
| GET | `/company/jobs` | List company-owned or company-matched postings |
| POST | `/company/jobs` | Create a manual company posting |
| GET | `/company/jobs/{job_id}` | Company posting detail |
| PATCH | `/company/jobs/{job_id}` | Update a manual company posting |
| DELETE | `/company/jobs/{job_id}` | Hide/delete a manual company posting |

Response includes:

- `company_id`, `company_name`, `business_number`
- `received_count`, `pending_count`, `posting_count`
- `applicants[]` with applicant, job, resume, status, applied date, and stored match-score fields

## Resumes

| Method | Path | Description |
|---|---|---|
| POST | `/resumes` | Upload PDF/PNG/JPG/JPEG/GIF resume, max 10MB |
| GET | `/resumes` | Current user's resume list |
| GET | `/resumes/{resume_id}` | Resume detail and parsed data |
| GET | `/resumes/{resume_id}/file` | Stream original file |
| DELETE | `/resumes/{resume_id}` | Soft-delete resume and remove file |

DOCX uploads are intentionally blocked. Legacy DOCX records fall back to parsed text/data rather than browser-native preview.

## Interview Practice

OpenAI-based interview practice uses parsed resume data, structured projects, structured cover letter sections, and server-side official reference materials.

Rules:

- Session creation calls OpenAI once and stores exactly 5 questions.
- Answer submission calls OpenAI once for one question.
- Session lookup does not call OpenAI.
- OpenAI Web Search tools are not used.

### POST `/resumes/{resume_id}/interview-sessions`

Creates an interview practice session for the current user's parsed resume.

### GET `/resumes/{resume_id}/interview-sessions/{session_id}`

Returns a saved session, questions, and answers for the current user.

### POST `/resumes/{resume_id}/interview-questions/{question_id}/answer`

Request:

```json
{ "answer": "My answer..." }
```

Response includes score, verdict, strengths, missing points, correct/different points, feedback, improved answer, references used, and model.

## Admin Users And Resumes

| Method | Path | Description |
|---|---|---|
| GET | `/admin/users` | Admin user list with role/search filters |
| GET | `/admin/users/{user_id}` | Admin user detail with resumes |
| GET | `/admin/users/resumes/{resume_id}` | Resume detail with structured data |
| PATCH | `/admin/users/resumes/{resume_id}` | Update title, raw text, parsed data, and structured data |
| GET | `/admin/users/resumes/{resume_id}/file` | Stream original file |
| GET | `/admin/stats` | Admin dashboard stats |

`GET /admin/users` supports role-specific search fields for ADMIN, USER, and COMPANY.

## Admin Leave Requests

RBAC is applied only to the new leave APIs. Existing admin-level gates remain unchanged.

| Method | Path | Permission | Description |
|---|---|---|---|
| POST | `/admin/leave` | `LEAVE_REQUEST` | Create a leave request |
| GET | `/admin/leave/me` | `LEAVE_REQUEST` | List current admin's leave requests |
| GET | `/admin/leave/pending` | `LEAVE_APPROVE` | List requests assigned to the current approver |
| PATCH | `/admin/leave/{id}/approve` | `LEAVE_APPROVE` | Approve a pending request |
| PATCH | `/admin/leave/{id}/reject` | `LEAVE_APPROVE` | Reject a pending request with a reason |
| PATCH | `/admin/leave/{id}/request-change` | `LEAVE_APPROVE` | Ask the requester to change the schedule (keeps the days reserved) |
| PATCH | `/admin/leave/{id}/cancel` | `LEAVE_REQUEST` | Cancel a pending/change-requested request or request cancellation after approval |
| PATCH | `/admin/leave/{id}/cancel-approve` | `LEAVE_APPROVE` | Approve a cancellation request |
| PATCH | `/admin/leave/{id}/cancel-reject` | `LEAVE_APPROVE` | Reject a cancellation request and keep the approved leave active |
| PATCH | `/admin/leave/{id}/resubmit` | `LEAVE_REQUEST` | Resubmit after a change request (recomputes days, returns to `PENDING`) |

Leave types:

- `ANNUAL`, `AM_HALF`, `PM_HALF`, `SICK`, `FAMILY_EVENT`, `OFFICIAL`, `COMPENSATORY`

Statuses:

- `PENDING`, `APPROVED`, `REJECTED`, `CANCELED`, `CANCEL_REQUESTED`, `CHANGE_REQUESTED`

Approval-line rules:

- `MEMBER` request -> same-team `LEAD`
- `LEAD` request -> `SUPER_ADMIN`
- `SUPER_ADMIN` request -> another `SUPER_ADMIN`
- The requester cannot approve their own request.

Schedule-change flow:

- An approver can answer a `PENDING` request with `request-change` instead of approve/reject; status becomes `CHANGE_REQUESTED`, the reason is stored, and the reserved days stay in `pending_days`.
- The requester then `resubmit`s with revised dates/type/reason (days are recomputed and the request returns to `PENDING` for re-approval) or `cancel`s it (reserved days are restored).
- When an approved request is canceled by the requester, an approver can `cancel-approve` to restore used days or `cancel-reject` to return it to `APPROVED` without changing balances.

Balance rules:

- Create request: `pending_days` increases and `remaining_days` decreases.
- Approve: `pending_days` decreases and `used_days` increases.
- Reject or cancel before approval: `pending_days` decreases and `remaining_days` increases.
- Approve cancellation after approval: `used_days` decreases and `remaining_days` increases.
