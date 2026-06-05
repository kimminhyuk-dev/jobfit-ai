# API_SPEC

Do not include secrets, API keys, tokens, or `.env` values in this document.

## Common

Error response shape:

```json
{ "code": "AUTH_001", "message": "...", "details": [] }
```

Main error code groups:

- `COMMON_001`, `COMMON_404`, `COMMON_405`, `COMMON_500`
- `AUTH_001~007`
- `CATEGORY_001~002`, `POST_001~002`
- `JOB_001~005`, `JOB_SOURCE_001`, `BATCH_001~002`, `CODE_001`
- `RESUME_001~003`, `RESUME_006`
- `OPENAI_API_KEY_MISSING`
- `INTERVIEW_SESSION_NOT_FOUND`
- `INTERVIEW_QUESTION_NOT_FOUND`
- `INTERVIEW_QUESTION_GENERATION_FAILED`
- `INTERVIEW_ANSWER_EVALUATION_FAILED`

## Auth `/auth`

| Method | Path | Description |
|---|---|---|
| POST | `/auth/signup` | Create user, issue access token, set refresh cookie |
| POST | `/auth/login` | Login |
| POST | `/auth/refresh` | Validate refresh token and issue new access token |
| POST | `/auth/logout` | Revoke refresh token and clear cookie |
| GET | `/auth/me` | Current user |
| PATCH | `/auth/me` | Update name/password |

## Categories And Posts

Categories:

- `GET /categories`
- `POST /categories` ADMIN
- `GET /categories/{id}`
- `PATCH /categories/{id}` ADMIN
- `DELETE /categories/{id}` ADMIN

Posts:

- `GET /posts?offset&limit&category_id`
- `POST /posts` ADMIN
- `GET /posts/{id}`
- `PATCH /posts/{id}` ADMIN
- `DELETE /posts/{id}` ADMIN

## Jobs

- `GET /jobs?source=ALIO&keyword=&data_source=PRODUCTION&page=1&size=20`
- `POST /admin/job-sources/alio/collect` ADMIN
- `POST /admin/jobs/sources/work24/collect` ADMIN, currently records BLOCKED history without external calls while pending approval
- `POST /admin/jobs/sources/mock/load` ADMIN

`job_postings.data_source`: `PRODUCTION`, `MOCK`, `MANUAL`.

## Resumes

| Method | Path | Description |
|---|---|---|
| POST | `/resumes` | Upload PDF/DOCX/TXT resume, max 10MB |
| GET | `/resumes` | Current user's resume list |
| GET | `/resumes/{id}` | Resume detail and parsed data |
| GET | `/resumes/{id}/file` | Stream original file |
| DELETE | `/resumes/{id}` | Soft-delete resume and remove file |

## Interview Practice

OpenAI-based interview practice uses parsed resume data, structured projects, structured cover letter sections, and server-side official reference materials.

OpenAI calls are user-triggered only:

- Session creation calls OpenAI once to generate 5 questions and stores them.
- Answer submission calls OpenAI once for one question.
- Session lookup does not call OpenAI.

OpenAI Web Search tools are not used.

### POST `/resumes/{resume_id}/interview-sessions`

Creates an interview practice session for the current user's parsed resume.

Response:

```json
{
  "session_id": 1,
  "resume_id": 3,
  "status": "IN_PROGRESS",
  "model": "gpt-5-mini",
  "total_score": null,
  "max_score": 100,
  "questions": [
    {
      "question_id": 11,
      "display_order": 1,
      "question": "Explain the most important technical decision in your project.",
      "question_type": "PROJECT",
      "source": "project",
      "intent": "Check project contribution and reasoning.",
      "difficulty": "BASIC",
      "expected_keywords": ["role", "tradeoff", "result"],
      "official_references": [],
      "max_score": 20,
      "answer": null
    }
  ]
}
```

### GET `/resumes/{resume_id}/interview-sessions/{session_id}`

Returns a saved session, questions, and answers for the current user. This endpoint does not call OpenAI.

### POST `/resumes/{resume_id}/interview-questions/{question_id}/answer`

Request:

```json
{ "answer": "My answer..." }
```

Response:

```json
{
  "answer_id": 101,
  "question_id": 11,
  "user_answer": "My answer...",
  "score": 12,
  "max_score": 20,
  "verdict": "PARTIAL",
  "strengths": ["Correct high-level direction."],
  "missing_points": ["Needs more detail about tradeoffs."],
  "incorrect_points": [],
  "feedback": "Specific feedback for improvement.",
  "reference_based_answer": "A stronger answer would include context, tradeoff, action, and result.",
  "official_references_used": [],
  "model": "gpt-5-mini"
}
```

## Admin Users And Resumes

| Method | Path | Description |
|---|---|---|
| GET | `/admin/users` | User list |
| GET | `/admin/users/{id}` | User detail with resumes |
| GET | `/admin/users/resumes/{id}` | Resume detail with structured projects and cover letter sections |
| PATCH | `/admin/users/resumes/{id}` | Update title, raw text, parsed data, and structured data |
| GET | `/admin/users/resumes/{id}/file` | Stream original file |
| GET | `/admin/stats` | Admin dashboard stats |

## Database Notes

- `users`, `refresh_tokens`
- `categories`, `posts`
- `job_postings`, `job_sources`, `batch_job_runs`
- `common_code_groups`, `common_codes`
- `resumes`
- `resume_projects`
- `resume_cover_letter_sections`
- `resume_interview_sessions`
- `resume_interview_questions`
- `resume_interview_answers`
