# ARCHITECTURE

## 백엔드 레이어

```
api/ → service/ → repository/ → model/
```

| 계층 | 역할 |
|---|---|
| `api/` | HTTP 요청 수신·응답 반환만 |
| `services/` | 비즈니스 로직 전담 |
| `repositories/` | DB 접근만 |
| `models/` | SQLAlchemy ORM |
| `schemas/` | Pydantic DTO (ORM과 분리) |
| `core/` | config, database, security, error_codes, exceptions |

## 프론트엔드 구조

```
src/app/          Next.js 16 App Router 경로
src/screens/      페이지 단위 로직 + 컴포넌트 조합
src/components/   공통 UI (shadcn/ui 패턴)
src/api/          백엔드 통신 모듈 + 공통 타입
src/stores/       인증 상태 (authStore)
src/lib/          공통 유틸
```

## 통신 규칙

- REST API, JSON 응답
- 인증: JWT Access Token → `Authorization: Bearer`, Refresh Token → HttpOnly Cookie
- 에러: `{ code, message, details? }` 공통 포맷
- `withCredentials: true` (Refresh Token Cookie 포함)

## 주요 DB 테이블

| 테이블 | 설명 |
|---|---|
| `users` | 사용자 (role: USER/ADMIN) |
| `refresh_tokens` | Refresh Token SHA-256 해시 저장 |
| `categories` / `posts` | Q&A 게시판 |
| `job_postings` | 채용공고 (data_source: PRODUCTION/MOCK/MANUAL) |
| `job_sources` | 수집원 상태 관리 |
| `batch_job_runs` | 수집 배치 이력 |
| `common_code_groups` / `common_codes` | ALIO 공통코드 |
| `resumes` | 이력서 메타 + 파싱 JSON |
| `resume_projects` | 프로젝트 구조화 (name/period/role/description/review/tech_stack) |
| `resume_cover_letter_sections` | 자기소개서 소제목별 구조화 (title/content) |
