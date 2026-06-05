# HANDOFF

Keep this file current after each agent task. Do not record `.env` values, API keys, tokens, or secrets.

## Project

- Name: jobfit-ai
- Goal: AI-assisted resume and job-posting matching platform.
- Backend: FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS v4
- Current branch: `codex-resume-api-hardening`

## Current State

Implemented OpenAI-based resume interview practice.

- Users can create an interview practice session from a parsed resume.
- Session creation calls OpenAI once and persists exactly 5 generated questions.
- Session lookup returns saved questions and submitted answers without calling OpenAI.
- Users can submit one answer per question for OpenAI scoring and feedback.
- Answer evaluation stores score, verdict, strengths, missing points, incorrect points, feedback, reference-based answer, and official references used.
- Official references are limited to server-side reference material. The OpenAI Web Search tool is not used.
- Claude interview-question code was removed from the active code path.

## API

New endpoints:

- `POST /resumes/{resume_id}/interview-sessions`
- `GET /resumes/{resume_id}/interview-sessions/{session_id}`
- `POST /resumes/{resume_id}/interview-questions/{question_id}/answer`

Existing resume upload/list/detail/file/delete endpoints remain.

## Database

New Alembic migration:

- `backend/alembic/versions/i1j2k3l4m5n6_add_resume_interview_practice_tables.py`

New tables:

- `resume_interview_sessions`
- `resume_interview_questions`
- `resume_interview_answers`

## Main Files Changed

Backend:

- `backend/app/api/resumes.py`
- `backend/app/core/config.py`
- `backend/app/models/resume_interview.py`
- `backend/app/repositories/interview_practice_repository.py`
- `backend/app/services/interview_practice_service.py`
- `backend/app/services/llm/openai_client.py`
- `backend/app/prompts/resume_interview.py`
- `backend/app/prompts/interview_references.py`
- `backend/app/schemas/resume_interview.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/i1j2k3l4m5n6_add_resume_interview_practice_tables.py`

Frontend:

- `frontend/src/api/types.ts`
- `frontend/src/api/resumes.ts`
- `frontend/src/screens/user/ResumesPage.tsx`

Removed:

- `backend/app/services/interview_question_service.py`
- `backend/app/services/llm/claude_client.py`

## Verification

Completed:

- `cd backend; python -m compileall app`
- `cd backend; .\.venv\Scripts\python.exe -m alembic upgrade head`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

## Latest Fix Notes

- Reduced OpenAI structured output schemas to a conservative strict JSON Schema subset.
- Replaced mojibake prompt text with clear ASCII instructions while still requiring Korean model output.
- Increased `openai_max_output_tokens` default to 6000 and made question generation enforce a 6000-token minimum even if local env config is lower.
- Added concise-output prompt rules to avoid truncated 5-question JSON.
- Added safe OpenAI SDK error logging without printing keys or request headers.
- Re-verified with `cd backend; python -m compileall app`.

## Latest UI / Evaluation Format Notes

- Korean-localized visible interview practice and resume page labels.
- Answer evaluation display now uses the order: score, strengths, missing points, improved answer, correct/different points.
- Answer evaluation prompt now requires concise factual bullets and adds `correct_points` / `different_points` to the structured output.
- Backend clamps strengths and missing points to 2 items, correct/different points to 1 item, and keeps feedback/improved answers short.
- Re-verified with:
  - `cd backend; python -m compileall app`
  - `cd frontend; npm run lint`
  - `cd frontend; npm run build`
