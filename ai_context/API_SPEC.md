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

Create request:

```json
{ "job_id": 1, "resume_id": 10 }
```

Duplicate active applications for the same `(user_id, job_id)` return `APPLICATION_001`.

## Company

| Method | Path | Description |
|---|---|---|
| GET | `/company/dashboard` | COMPANY-only dashboard with counts and received applicants |

Response includes:

- `company_id`, `company_name`, `business_number`
- `received_count`, `pending_count`, `posting_count`
- `applicants[]` with applicant, job, resume, status, and applied date

## Resumes

| Method | Path | Description |
|---|---|---|
| POST | `/resumes` | Upload PDF/DOCX/TXT resume, max 10MB |
| GET | `/resumes` | Current user's resume list |
| GET | `/resumes/{resume_id}` | Resume detail and parsed data |
| GET | `/resumes/{resume_id}/file` | Stream original file |
| DELETE | `/resumes/{resume_id}` | Soft-delete resume and remove file |

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
