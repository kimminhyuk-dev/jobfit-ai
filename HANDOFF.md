# HANDOFF

AI 인수인계 기준 문서. 작업 완료 시마다 갱신한다. `.env` 값/비밀키 절대 기록 금지.

## 프로젝트 요약

- **목적**: AI 기반 이력서-채용공고 매칭 플랫폼 (포트폴리오)
- **백엔드**: FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL (Docker)
- **프론트엔드**: Next.js 16 App Router + React 19 + TypeScript + Tailwind CSS v4
- **인증**: Access Token(15분) + Refresh Token(14일) 모두 HttpOnly 쿠키, Refresh Token DB SHA-256 해시 저장
- **권한**: `users.role` → USER / ADMIN
- **환경**: Windows, PowerShell, Python 3.12

## 현재 브랜치

`codex-resume-api-hardening` — 이력서 API 하드닝 (schemas/services/repositories 정비)

## 완료된 기능

### 백엔드 API

| 도메인 | 엔드포인트 |
|---|---|
| 기본 | `GET /`, `GET /health`, `GET /health/db` |
| 인증 | `POST /auth/signup`, `/login`, `/refresh`, `/logout`, `GET /auth/me`, `PATCH /auth/me` |
| 게시판 | `GET/POST/PATCH/DELETE /categories/{id}`, `GET/POST/PATCH/DELETE /posts/{id}` |
| 채용공고 | `GET /jobs`, `POST /admin/job-sources/alio/collect`, `POST /admin/jobs/sources/mock/load` |
| 이력서 | `GET/POST/DELETE /resumes/{id}`, `GET /resumes/{id}/file` |
| 관리자 이력서 | `GET/PATCH /admin/users/resumes/{id}`, `GET /admin/users/resumes/{id}/file` |
| 관리자 사용자 | `GET /admin/users`, `GET /admin/users/{id}` |
| 관리자 통계 | `GET /admin/stats` |

### DB 테이블
`users`, `refresh_tokens`, `categories`, `posts`, `job_postings`, `job_sources`, `batch_job_runs`, `common_code_groups`, `common_codes`, `resumes`, `resume_projects`, `resume_cover_letter_sections`

### 이력서 파싱
- 파일 지원: PDF / DOCX / TXT, 최대 10MB
- 파싱 상태: `PENDING` / `COMPLETED` / `FAILED`
- 구조화 테이블: `resume_projects`(name/period/role/description/review/tech_stack), `resume_cover_letter_sections`(title/content)
- LLM(Gemini): 프로젝트 구조화 객체 배열, 자기소개서 소제목별 dict 반환
- rule-based 폴백 3단계, 자기소개서/프로젝트 섞임 후처리 보정

### 프론트엔드 화면
- 사용자: `/user/dashboard`, `/user/resumes`, `/user/jobs`, `/user/mock-jobs`, `/user/matches`
- 관리자: `/admin/dashboard`, `/admin/categories`, `/admin/posts`, `/admin/jobs`, `/admin/mock-jobs`, `/admin/users`
- 관리자 이력서 편집: `ResumeParsedDataEditor` — 프로젝트 카드 / 자기소개서 목차 카드 / 수정 모드 지원

### 채용공고
- ALIO 공공기관 API 실 수집 (ACTIVE)
- Work24 — 키 발급됐으나 일반 API 제한으로 PENDING_APPROVAL 보류
- `job_postings.data_source`: `PRODUCTION` / `MOCK` / `MANUAL`

## 최근 검증 (2026-05-06)

- `resume_projects`, `resume_cover_letter_sections` 구조화 테이블 도입, Alembic `h1i2j3k4l5m6` 적용
- 이력서 조회 시 자동 재파싱(LLM 호출) 제거 — `_refresh_parsed_data_if_empty()` 호출 삭제
- `python -m compileall app` 통과
- `alembic upgrade head` 통과
- `npm run lint` 통과 / `npm run build` 통과 (20개 App Router 경로)

## 다음 작업 (우선순위 순)

1. Claude API 연동 — 이력서 vs 공고 강점·약점·개선 제안 분석
2. 벡터 임베딩 — sentence-transformers + pgvector 매칭 점수 계산
3. 채용공고 페이지네이션 (현재 size=50 고정)
4. 프론트엔드 toast / field error 표시 고도화
5. ALIO 공통코드 동기화 배치 구현 여부 결정
6. 결제 PG 연동 (토스페이먼츠 등)

## 주요 파일 위치

```
backend/app/
  api/         auth.py, resumes.py, admin_users.py, admin_jobs.py, jobs.py, categories.py, posts.py, deps.py
  core/        config.py, database.py, security.py, error_codes.py, exception_handlers.py, exceptions.py
  models/      user.py, resume.py, resume_project.py, resume_cover_letter_section.py, job_posting.py, ...
  repositories/ resume_repository.py, user_repository.py, job_posting_repository.py, ...
  schemas/     resume.py, auth.py, user.py, job_collection.py, ...
  services/    resume_service.py, resume_parser.py, alio_collection_service.py, user_service.py, ...
frontend/src/
  app/         (Next.js App Router 경로)
  screens/     user/ResumesPage.tsx, admin/AdminUsersPage.tsx, ...
  components/  resume/ResumeParsedDataEditor.tsx, layout/UserLayout.tsx, AdminLayout.tsx
  api/         client.ts, types.ts, resumes.ts, jobs.ts, auth.ts
  stores/      authStore.tsx
```
