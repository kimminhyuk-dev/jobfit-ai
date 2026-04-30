이 문서는 ChatGPT, Claude, Claude Code 등 다른 AI에게 프로젝트 상태를 한 번에 전달하기 위한 최신 브리핑 문서다.
프로젝트의 AI 인수인계 기준본은 루트의 이 `HANDOFF.md` 하나로 관리한다.

## AI 작업 규칙

- 이 파일은 작업 완료 시마다 최신 상태로 갱신한다.
- 기존에 건드리지 않은 기능 설명, 결정사항, 완료 내역은 유지한다.
- 수정한 기능이나 새로 만든 기능만 관련 섹션에 추가/수정한다.
- 오래된 내용이 실제 코드와 충돌할 때만 최소 범위로 고친다.
- `.env` 값, 비밀키, 실제 토큰, 비밀번호는 절대 기록하지 않는다.
- 코드 변경 전에는 현재 파일 상태와 `git status`를 확인한다.
- 사용자가 만든 변경사항을 되돌리지 않는다.
- 작업 완료 후에는 검증한 명령과 결과를 `최근 검증`에 적는다.

## 프로젝트 요약

- 프로젝트명: jobfit-ai
- 목적: AI 기반 이력서-채용공고 매칭 플랫폼
- 백엔드: FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL
- 프론트엔드: React 19, TypeScript, Vite 8, Tailwind CSS v4 기반 초기 구현 완료
- 인증 방식: JWT Access Token + HttpOnly Refresh Token Cookie
- 권한 방식: `users.role` 기반 USER / ADMIN
- 개발 환경: Windows, PowerShell, Python 3.12 계열

## 현재 상태

- GitHub 저장소와 로컬 저장소 연결 완료
- `frontend` / `backend` 폴더 생성 완료
- 백엔드 FastAPI 레이어드 구조 구성 완료
  - `app/api`
  - `app/core`
  - `app/models`
  - `app/repositories`
  - `app/schemas`
  - `app/services`
- PostgreSQL은 Docker 기반으로 사용
- `users` 테이블용 User 모델 생성 완료
- Alembic 첫 마이그레이션 적용 완료
- 인증 API 구현 완료
- 카테고리 기반 Q&A 게시판 CRUD API 구현 완료
- 카테고리/게시글 생성·수정·삭제는 ADMIN만 가능
- 일반 USER는 카테고리/게시글 조회만 가능
- 공통 에러코드 기반 API 에러 응답 체계 구현 완료
- 프론트엔드 React 앱 초기 구현 완료
  - 로그인/회원가입 화면과 인증 API 연결
  - Access Token은 localStorage, Refresh Token은 HttpOnly Cookie 기반으로 사용
  - 사용자/관리자 보호 라우트 구성
  - 사용자 대시보드/이력서/채용공고/매칭 화면은 mock 데이터 기반 UI 구현
  - 관리자 대시보드/카테고리/Q&A 게시글 화면은 mock 데이터 기반 UI 구현
- 프론트엔드 공통 API 클라이언트가 백엔드 공통 에러 응답 `{ code, message, details }`를 수신하도록 구성됨
- 프론트엔드 계획 스택 반영 완료
  - React 19 적용
  - Vite 8 적용
  - Tailwind CSS v4 및 `@tailwindcss/vite` 적용
  - TanStack Query Provider 적용
  - React Hook Form + Zod 기반 로그인/회원가입 폼 검증 적용
  - shadcn/ui 방식의 `Button`, `Input`, `Alert` 공통 컴포넌트 추가
  - ESLint 9 flat config 기반 프론트엔드 lint 설정 적용
- 루트 AI 에이전트 지시 문서 생성 완료 (AGENTS.md / CLAUDE.md / GEMINI.md)
- AI 인수인계 문서는 루트 `HANDOFF.md`로 단일화 완료
- 워크넷/고용24 채용공고 도메인 DB 스키마 추가 (Phase 1)
- 워크넷/고용24 채용정보 수집 클라이언트, 저장 서비스, 관리자 수동 수집 API 추가 (Phase 2)
- Work24/고용24는 키는 발급됐으나 일반 사용자 API 사용 제한으로 `job_sources.status=PENDING_APPROVAL` 보류 처리
- ALIO 공공기관 채용정보 API를 현재 메인 공공기관 채용 수집원으로 전환
- 채용공고 수집원 상태 관리를 위한 `job_sources` 테이블 추가
- `job_postings`를 ALIO/WORK24/SARAMIN/MANUAL 확장형 저장소로 재사용하도록 컬럼 확장
- ALIO 코드 정의서 기준 `common_code_groups`, `common_codes` 테이블과 마이그레이션 추가
- `batch_job_runs`를 ALIO 수집 배치 이력까지 기록할 수 있도록 확장
- 관리자 수동 ALIO 수집 API와 사용자 채용공고 조회 API 추가
- ALIO 설정은 `.env`에서 `ALIO_BASE_URL`, `ALIO_API_KEY`만 관리하고 목록/상세 endpoint path는 코드 상수로 관리
- 기존 `.env`에 deprecated `ALIO_RECRUIT_LIST_URL`, `ALIO_RECRUIT_DETAIL_URL`이 남아 있어도 클라이언트에서 현재 코드 상수 기반 URL로 보정
- ALIO 목록 수집은 현재 동작하는 `/new/odaApiMng/recrutInquiryAjaxList.do` 응답 구조 기준으로 매핑

## 완료된 백엔드 기능

### 기본 앱

- `GET /`
- `GET /health`
- `GET /health/db`

### 인증

- `POST /auth/signup` — 회원가입, bcrypt 해시, Access Token 응답, Refresh Token HttpOnly Cookie
- `POST /auth/login` — 이메일/비밀번호 로그인
- `POST /auth/refresh` — Refresh Token 검증 후 새 토큰 발급
- `POST /auth/logout` — Refresh Token Cookie 삭제
- `GET /auth/me` — Bearer Access Token으로 현재 사용자 조회

### 게시글

- `GET /categories` — 활성 카테고리 목록 조회
- `POST /categories` — 관리자 카테고리 생성
- `GET /categories/{category_id}` — 활성 카테고리 상세 조회
- `PATCH /categories/{category_id}` — 관리자 카테고리 수정
- `DELETE /categories/{category_id}` — 관리자 카테고리 소프트 삭제
- `GET /posts` — Q&A 게시글 목록 조회
- `POST /posts` — 관리자 Q&A 게시글 생성
- `GET /posts/{post_id}` — 게시글 상세 조회
- `PATCH /posts/{post_id}` — 관리자 Q&A 게시글 수정
- `DELETE /posts/{post_id}` — 관리자 Q&A 게시글 소프트 삭제

### 공통 에러 처리

- API 에러 응답은 기본적으로 `{ "code": "...", "message": "..." }` 형태로 통일
- 입력값 검증 오류는 `COMMON_001` 코드와 함께 `details` 배열을 추가로 응답
- 인증/권한/카테고리/게시글 도메인 오류는 `AUTH_*`, `CATEGORY_*`, `POST_*` 에러코드로 구분

### 채용공고 도메인

- 채용공고 도메인 모델 (`job_postings`, `batch_job_runs`) - Phase 1 DB 구조
- Work24 채용정보 수집 (관리자 수동 수집 API)
- Work24 채용정보 수집은 일반 사용자 API 사용 제한으로 외부 API 호출 없이 `JOB_SOURCE_001` + `BLOCKED` 배치 이력 기록
- ALIO 공공기관 채용정보 수집 클라이언트와 관리자 수동 수집 API
- ALIO 기존 `/v1/recruit/list.do` 302 redirect 방어 및 현재 목록 JSON 응답 필드 매핑
- ALIO endpoint URL 환경 변수 deprecated 처리 및 `ALIO_BASE_URL` + 코드 상수 path 기반 URL 조립
- 사용자 채용공고 조회 API `GET /jobs`
- ALIO 코드 정의서 기반 공통코드 그룹/상세코드 테이블

### Mock 데이터 트랙 (data_source 컬럼)

- `job_postings.data_source` 컬럼 추가 (`VARCHAR(20)`, `server_default='PRODUCTION'`, 인덱스 포함)
  - `PRODUCTION`: 실제 공공데이터 API 수집 데이터
  - `MOCK`: 시연/매칭 검증용 Mock 데이터 (IT 회사명 등)
  - `MANUAL`: 향후 사용자 수동 입력 (예약)
- 기존 수집 서비스(`save_from_work24`, `save_from_alio`)에 `data_source` 파라미터 추가 (기본 `"PRODUCTION"`)
- `JobPostingRepository.list_by_filter`에 `data_source` 필터 추가
- `GET /jobs` API에 `data_source` 쿼리 파라미터 추가
- `MockLoaderService` 신설: `backend/data/mock_work24_jobs.json` → `data_source="MOCK"` 저장
- `POST /admin/jobs/sources/mock/load` 관리자 API 추가
- Alembic 마이그레이션: `b8050fd5e470_add_data_source_column_to_job_postings.py`
  - `job_sources` unique constraint 제거 라인은 수동으로 제거됨 (기존 drift, 우리 작업 범위 아님)
- `backend/data/.gitkeep` 생성 (Mock JSON 파일 위치 예약)

### 관리자 대시보드 통계 API

- `GET /admin/stats` — 관리자 전용 통계 요약 (전체 사용자, 활성 카테고리, 총 게시글, 오늘 가입, 채용공고 수)
- `UserRepository.count_total()`, `count_today()` 추가
- `CategoryRepository.count_active()` 추가
- `PostRepository.count_total()` 추가
- `AdminStatsService`, `AdminStatsResponse` 스키마 신설

## 완료된 프론트엔드 기능

- Vite + React + TypeScript 프로젝트 구성
- Tailwind CSS v4 기반 전역 스타일과 사용자/관리자 레이아웃 구성
- React 19 기반으로 업그레이드
- Vite 8 및 `@tailwindcss/vite` 기반 빌드 설정 적용
- ESLint 9 flat config 기반 lint 설정 적용
- 개발 중 Vite가 5174 포트로 올라가는 경우를 고려해 백엔드 기본 CORS 허용 origin에 `localhost/127.0.0.1:5174` 추가
- axios API 클라이언트 구성
  - 기본 API URL: `VITE_API_URL` 또는 `http://localhost:8000`
  - `withCredentials: true`로 Refresh Token Cookie 포함
  - Access Token을 `Authorization: Bearer` 헤더에 자동 주입
- TanStack Query `QueryClientProvider` 구성
- 로그인/회원가입 화면 구현 및 `/auth/login`, `/auth/signup`, `/auth/me`, `/auth/logout` 연결
- 로그인/회원가입 화면은 React Hook Form + Zod로 클라이언트 검증 처리
- 공통 에러 응답 타입과 회원가입 validation `details` 필드 매핑 정리
- shadcn/ui 패턴 기반 공통 UI 컴포넌트 추가 (`Button`, `Input`, `Alert`)
- 사용자 채용공고 화면(`/user/jobs`)을 실제 `GET /jobs?source=ALIO` API와 연결 완료
  - TanStack Query 기반 데이터 패칭
  - 공고 목록(좌) + 상세(우) 마스터-디테일 레이아웃 유지
  - 표시 필드: 공고 제목, 기관명, 출처, 고용형태, 근무지, 마감일, 경력, 학력, 기관유형, 주무부처, NCS 분류
  - 급여: 숫자 미제공 시 "공고문 참조" 표시
  - source_url이 있으면 원문 공고 링크 제공
  - 로딩/에러 상태 처리
- 사용자 라우트: `/user/dashboard`, `/user/resumes`, `/user/jobs`, `/user/matches`
- 관리자 라우트: `/admin/dashboard`, `/admin/categories`, `/admin/posts`, `/admin/jobs`
- 관리자 대시보드 `GET /admin/stats` 연결 완료: 전체 사용자·활성 카테고리·총 게시글·오늘 가입·채용공고 수 실데이터 표시, 로딩 스켈레톤·에러 배너 포함
- 관리자 채용공고 화면(`/admin/jobs`) 신설: 소스 탭 필터(전체/ALIO/WORK24/SARAMIN/MANUAL), 상태 배지(OPEN/CLOSED/EXPIRED/HIDDEN), 마스터-디테일 레이아웃, 수집 메타 패널 포함
- 관리자 라우트는 `user.role === 'ADMIN'`일 때만 접근 가능

- `frontend/src/api/admin.ts`
- `frontend/src/pages/admin/AdminJobsPage.tsx`
- `backend/app/services/mock_loader_service.py`
- `backend/data/mock_work24_jobs.json` (사용자가 배치 필요)

## 주요 파일

- `backend/app/main.py`
- `backend/app/api/auth.py`
- `backend/app/api/admin_jobs.py`
- `backend/app/api/jobs.py`
- `backend/app/api/categories.py`
- `backend/app/api/deps.py`
- `backend/app/api/posts.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/core/error_codes.py`
- `backend/app/core/exception_handlers.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/security.py`
- `backend/app/models/base.py`
- `backend/app/models/batch_job_run.py`
- `backend/app/models/category.py`
- `backend/app/models/common_code.py`
- `backend/app/models/job_source.py`
- `backend/app/models/job_posting.py`
- `backend/app/models/post.py`
- `backend/app/models/user.py`
- `backend/app/repositories/category_repository.py`
- `backend/app/repositories/batch_job_run_repository.py`
- `backend/app/repositories/job_source_repository.py`
- `backend/app/repositories/job_posting_repository.py`
- `backend/app/repositories/post_repository.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/schemas/auth.py`
- `backend/app/schemas/category.py`
- `backend/app/schemas/job_collection.py`
- `backend/app/schemas/post.py`
- `backend/app/schemas/user.py`
- `backend/app/services/category_service.py`
- `backend/app/services/alio_collection_service.py`
- `backend/app/services/job_source_service.py`
- `backend/app/services/job_posting_service.py`
- `backend/app/services/post_service.py`
- `backend/app/services/user_service.py`
- `backend/app/services/work24_collection_service.py`
- `backend/app/services/job_sources/alio_client.py`
- `backend/app/services/job_sources/work24_client.py`
- `backend/alembic/versions/c1d2e3f4a5b6_add_alio_job_source_and_common_codes.py`
- `backend/alembic/versions/d2e3f4a5b6c7_add_job_sources_table.py`
- `backend/alembic/versions/4f6a7b8c9d10_add_categories_and_admin_role.py`
- `backend/alembic/versions/b9a9c0967b9a_add_job_postings_and_batch_job_runs_.py`
- `backend/alembic/versions/3a2b1c4d5e6f_create_posts_table.py`
- `backend/alembic/versions/8dad372a1f24_create_users_table.py`
- `backend/.env.example`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/api/auth.ts`
- `frontend/src/api/types.ts`
- `frontend/src/lib/utils.ts`
- `frontend/src/stores/authContext.ts`
- `frontend/src/stores/authStore.tsx`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/input.tsx`
- `frontend/src/components/ui/alert.tsx`
- `frontend/src/api/jobs.ts`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/SignupPage.tsx`
- `frontend/src/components/layout/UserLayout.tsx`
- `frontend/src/components/layout/AdminLayout.tsx`
- `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`
- `HANDOFF.md`
- `ai_context/API_SPEC.md`

## 최근 검증

2026-04-30 Mock 데이터 트랙 추가:

- `python -m compileall app` 통과 (job_posting.py, job_posting_service.py, mock_loader_service.py 등 포함)
- `POST /admin/jobs/sources/mock/load` 라우트 등록 확인
- 전체 관리자 라우트 확인: `/admin/job-sources/alio/collect`, `/admin/jobs/sources/work24/collect`, `/admin/jobs/sources/mock/load`, `/admin/stats`
- Alembic 마이그레이션 `b8050fd5e470_add_data_source_column_to_job_postings.py` 생성 확인
  - `ALTER TABLE job_postings ADD COLUMN data_source VARCHAR(20) NOT NULL DEFAULT 'PRODUCTION'`
  - `CREATE INDEX ix_job_postings_data_source`
- `alembic upgrade head` 미실행 (사용자 마이그레이션 검토 후 적용 예정)

2026-04-30 관리자 대시보드·채용공고 작업 완료:

- `python -m compileall app` 통과 (admin_stats.py, admin_stats_service.py, user/category/post_repository.py 변경 포함)
- `npm run lint` 통과 (경고 0개)
- `npm run build` 통과 (232 modules)
- `GET /admin/stats` FastAPI 라우터 등록 확인
- 관리자 대시보드 실데이터 연결 및 AdminJobsPage 신설 확인

2026-04-30 기준 확인 완료:

- 워크넷/고용24 채용공고 도메인 모델 추가 후 `.\.venv\Scripts\python.exe -m compileall app` 통과
- Alembic 자동 생성으로 `b9a9c0967b9a_add_job_postings_and_batch_job_runs_.py` 생성 확인
- 마이그레이션 파일에서 `batch_job_runs`, `job_postings` 테이블 생성 확인
- `job_postings.collect_run_id` → `batch_job_runs.run_id` 외래키 생성 확인
- `uq_job_postings_source` 유니크 제약조건과 주요 인덱스 생성 확인
- `status`, `collection_status`, `embedding_status`, 카운트 컬럼, `is_deleted` 등 server default 반영 확인
- `alembic upgrade head`는 이번 작업에서 실행하지 않음 (사용자 검토 후 적용 예정)
- 워크넷/고용24 Phase 2 추가 후 `.\.venv\Scripts\python.exe -m compileall app` 통과
- FastAPI 라우트 확인 명령으로 `POST /admin/jobs/sources/work24/collect` 등록 확인
- 실제 Work24 외부 API 호출 테스트는 자동 실행하지 않음 (사용자 수동 테스트 예정)
- ALIO 전환 구조 추가 후 `.\.venv\Scripts\python.exe -m compileall app` 통과
- `.\.venv\Scripts\alembic.exe heads` 결과 `c1d2e3f4a5b6 (head)` 확인
- FastAPI 라우트 확인 명령으로 `POST /admin/job-sources/alio/collect`, `POST /admin/jobs/sources/work24/collect`, `GET /jobs` 등록 확인
- Alembic 마이그레이션 `c1d2e3f4a5b6_add_alio_job_source_and_common_codes.py` 생성 확인
- 실제 ALIO 외부 API 호출 테스트는 API 키가 필요하므로 자동 실행하지 않음
- `.env`는 `git status --short`에 포함되지 않고, `.env.example`만 변경 대상임을 확인
- Work24 비활성/보류 처리 수정 후 `.\.venv\Scripts\python.exe -m compileall app` 통과
- Work24 XML 오류 응답 방어 로직 확인: `resultCode=146`, `resultMsg=권한 제한` 샘플이 `Work24ClientError`로 처리됨
- FastAPI 라우트 확인 명령으로 `POST /admin/job-sources/alio/collect`, `POST /admin/jobs/sources/work24/collect`, `GET /jobs` 등록 재확인
- Work24 보류 처리를 환경변수 값과 무관하게 강제하도록 수정 후 `.\.venv\Scripts\python.exe -m compileall app` 통과
- Work24 보류 처리 단위 확인: 동일 `idempotency_key`가 있어도 기존 성공 run 재사용 없이 차단 결과를 만들고 외부 호출 없음 확인
- 수집원 상태 관리용 `job_sources` 테이블 마이그레이션 `d2e3f4a5b6c7_add_job_sources_table.py` 생성 확인
- `.\.venv\Scripts\alembic.exe heads` 결과 `d2e3f4a5b6c7 (head)` 확인
- `.\.venv\Scripts\alembic.exe upgrade head` 통과
- `job_sources` seed 확인: `ALIO=ACTIVE`, `WORK24=PENDING_APPROVAL`, `SARAMIN=DISABLED`, `MANUAL=ACTIVE`
- source 상태 기반 Work24 차단 검증: 실제 DB 세션에서 `source=WORK24`, `status=BLOCKED`, `collected_count=0`, `inserted_count=0`, `updated_count=0`, `skipped_count=1`, `failed_count=0`, `error_code=JOB_SOURCE_001` 확인
- ALIO 기존 `/v1/recruit/list.do` URL이 `https://opendata.alio.go.kr/new`로 302 redirect되어 HTML을 반환하는 문제 확인
- ALIO 목록 수집 URL을 현재 동작하는 `/new/odaApiMng/recrutInquiryAjaxList.do`로 보정하고 실제 응답 필드(`recrutPblntSn`, `recrutPbancTtl`, `instNm` 등) 매핑 반영
- ALIO 클라이언트 직접 검증: `fetch_recruit_list(start_page=1, display=2)` 결과 2건 파싱 확인
- ALIO 수집 서비스 검증: 실제 DB 세션에서 `run_id=8`, `status=SUCCESS`, `collected_count=2`, `inserted_count=2`, `failed_count=0` 확인
- ALIO 설정 구조 정리 후 `.env`의 endpoint 전체 URL 의존 제거: `ALIO_BASE_URL` + `RECRUIT_LIST_PATH`/`RECRUIT_DETAIL_PATH` 코드 상수 기반 URL 조립으로 변경
- ALIO deprecated endpoint env 방어 검증: 기존 `.env`에 구 `ALIO_RECRUIT_LIST_URL`이 남아 있어도 실제 수집 `run_id=9`, `status=SUCCESS`, `collected_count=1`, `skipped_count=1`, `failed_count=0` 확인
- `GET /jobs?source=ALIO&page=1&size=5` TestClient 검증: HTTP 200, `total=2`, `items_count=2` 확인
- `GET /jobs?source=ALIO` 조회 경로 확인: 저장 데이터 0건 상태에서 정상 조회 처리 확인
- `.\.venv\Scripts\python.exe -m compileall app` 재검증 통과
- 프론트엔드 채용공고 화면 `GET /jobs?source=ALIO` 연결 후 `npm run lint` 통과 (경고 0개)
- 프론트엔드 채용공고 화면 `GET /jobs?source=ALIO` 연결 후 `npm run build` 통과 (230 modules)
- Alembic DB 상태: `d2e3f4a5b6c7 (head)` - upgrade 불필요
- 프론트엔드 `npm run lint` 통과
- 프론트엔드 `npm run build` 통과
- 프론트엔드 `npm audit` 결과 취약점 0개 확인
- `git diff --check` 결과 공백 오류 없음
- `.env`는 `git status --short`에 포함되지 않음 확인

2026-04-29 기준 확인 완료:

- `python -m compileall app` 통과
- 인증 라우트 전체 확인 완료 (`/auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`)
- 카테고리 라우트 전체 확인 완료 (`/categories`, `/categories/{category_id}`)
- 게시글 라우트 전체 확인 완료 (`/posts`, `/posts/{post_id}`)
- Alembic upgrade head 완료: `4f6a7b8c9d10`
- bcrypt 해시·검증, Access Token 생성·검증 정상
- 실제 DB 세션 기반 인증 흐름 검증 완료 (회원가입 → 로그인 → 토큰 재발급 → 로그아웃)
- 실제 DB 세션 기반 게시글 CRUD 흐름 검증 완료 (생성 → 목록 → 상세 → 수정 → 삭제)
- 실제 DB 세션 기반 관리자 권한 흐름 검증 완료
  - 일반 USER 카테고리/게시글 생성 403
  - ADMIN 카테고리 생성/조회 및 게시글 생성/수정/삭제 성공
- 루트 `HANDOFF.md` 기준으로 AI 인수인계 문서 단일화 확인
- Swagger 기반 카테고리/Q&A 게시글 수동 테스트 완료 확인
- `.\.venv\Scripts\python.exe -m compileall app` 통과
- FastAPI TestClient로 공통 에러 응답 확인 완료
  - `GET /auth/me` 401 → `AUTH_001`
  - `GET /not-found` 404 → `COMMON_404`
  - `PUT /health` 405 → `COMMON_405`
  - `POST /auth/login` 검증 실패 422 → `COMMON_001`
- 프론트엔드 `npm run build` 통과
- 프론트엔드 `npm run lint` 통과
- React 19 / TanStack Query / React Hook Form / Zod / shadcn 스타일 컴포넌트 반영 후 `npm run lint` 통과
- React 19 / TanStack Query / React Hook Form / Zod / shadcn 스타일 컴포넌트 반영 후 `npm run build` 통과
- 프론트엔드 Vite 8 / Tailwind CSS v4 / ESLint 9 전환 후 `npm run lint` 통과
- 프론트엔드 Vite 8 / Tailwind CSS v4 / ESLint 9 전환 후 `npm run build` 통과
- 프론트엔드 `npm audit` 결과 취약점 0개 확인
- 프론트엔드 Vite dev server `http://127.0.0.1:5174` 기동 및 HTTP 200 응답 확인
- Docker PostgreSQL 컨테이너 `jobfit_postgres` healthy 확인
- 백엔드 `GET /health/db` 실제 HTTP 요청 결과 200 및 DB connected 확인
- 프론트 origin `http://127.0.0.1:5174` 기준 백엔드 CORS preflight 정상 확인
- 프론트 origin `http://127.0.0.1:5174` 기준 `GET /categories` 실제 HTTP 요청 200 확인
- 프론트 origin `http://127.0.0.1:5174` 기준 `GET /auth/me`, `POST /auth/login` 비인증/오인증 요청 401 정상 응답 및 CORS credential 헤더 확인

## 참고 사항

- 관리자 테스트 계정은 DB에서 `users.role = 'ADMIN'`으로 승격해서 사용한다.
  예: `UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';`
- 백그라운드 dev server 실행은 현재 도구 환경에서 프로세스가 바로 종료되어 유지되지 않는다.
- 포그라운드 실행은 정상 확인됨.
- 서버 실행 명령:

```powershell
cd C:\Users\USER\jobfit-ai\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- 프론트엔드 실행 명령:

```powershell
cd C:\Users\USER\jobfit-ai\frontend
npm run dev
```

- 현재 프론트엔드 구현 스택은 `package.json` 기준 React 19, Vite 8, Tailwind CSS v4이다.
- TanStack Query, React Hook Form, Zod, React Router v7, shadcn/ui 패턴 기반 공통 컴포넌트는 적용 완료.
- 로컬 Node 버전은 `v20.20.2`로 확인되었고, Tailwind CSS v4 native binding 이슈 없이 빌드가 통과한다.
- `frontend` dev server가 기본 5173 포트를 사용할 수 없을 때 5174로 뜰 수 있으므로, 백엔드 CORS 기본값과 `.env.example`은 5173/5174를 모두 포함한다.

## 다음 작업

1. 마이그레이션 검토 후 `alembic upgrade head` 실행
2. `backend/data/mock_work24_jobs.json` 파일 준비 후 `POST /admin/jobs/sources/mock/load` Swagger 테스트
3. DB 확인: `SELECT data_source, COUNT(*) FROM job_postings GROUP BY data_source;`
4. 프론트엔드: 사용자 채용공고 화면에 data_source 필터 추가 (Mock/실데이터 탭 분리)
5. 관리자 카테고리 화면을 실제 `/categories` API와 연결
6. 관리자 Q&A 게시글 화면을 실제 `/posts` API와 연결
7. 채용공고 페이지에 페이지네이션 추가 (현재 size=50/100 고정)
8. 매칭 기능(AI 매칭 점수, 스킬 분석) 구현
9. ALIO 코드 동기화 배치 (`ALIO_CODE_SYNC`) 구현 여부 결정

## 다른 AI에게 요청할 때 사용할 프롬프트

아래 문장을 ChatGPT, Claude, Claude Code에 붙여넣고 이 파일 내용을 함께 전달한다.

```md
아래는 내 프로젝트의 최신 HANDOFF 문서다.
이 내용을 기준으로 현재 상태를 파악하고 이어서 작업해줘.

중요 규칙:
- 기존에 건드리지 않은 내용은 유지해줘.
- 수정하거나 새로 만든 기능만 관련 문서와 코드에 반영해줘.
- 사용자가 만든 변경사항을 되돌리지 마.
- 작업 완료 후 HANDOFF.md의 현재 상태, 완료 기능, 최근 검증, 다음 작업만 필요한 만큼 업데이트해줘.
- .env 값이나 비밀키는 절대 출력하거나 문서에 쓰지 마.

[여기에 HANDOFF.md 전체 내용을 붙여넣기]
```

## Claude Code에게 줄 추가 지시

Claude Code처럼 로컬 파일을 직접 볼 수 있는 AI에게는 아래 지시를 함께 준다.

```md
먼저 `git status --short`로 현재 변경사항을 확인해줘.
그 다음 `HANDOFF.md`를 읽고 현재 작업 상태를 파악해줘.

작업할 때는:
- 사용자가 만든 변경사항을 되돌리지 말 것
- 요청받은 기능과 직접 관련된 파일만 수정할 것
- 기존에 건드리지 않은 HANDOFF 내용은 유지할 것
- 새로 구현하거나 수정한 내용만 HANDOFF에 반영할 것
- 작업 후 실행한 검증 명령과 결과를 HANDOFF의 `최근 검증`에 추가할 것
```
