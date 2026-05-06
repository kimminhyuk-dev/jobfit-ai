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
- 프론트엔드: Next.js 16 App Router, React 19, TypeScript, Tailwind CSS v4 기반 구현 완료
- 인증 방식: Access Token + Refresh Token 모두 HttpOnly 쿠키 저장 (localStorage 제거)
- Refresh Token은 DB(`refresh_tokens`)에 SHA-256 해시로 저장 — 취소(revocation)·재사용 감지(reuse detection) 지원
- 인증 방식: Access Token(15분) + Refresh Token(14일) 모두 HttpOnly 쿠키, Refresh Token은 DB에 SHA-256 해시 저장
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
- 프론트엔드 Next.js 앱 전환 완료
  - 로그인/회원가입 화면과 인증 API 연결
  - Access Token과 Refresh Token은 모두 HttpOnly Cookie 기반으로 사용
  - 사용자/관리자 보호 라우트 구성
  - 사용자 대시보드/채용공고/이력서 화면은 실제 API 연결 완료, 매칭 화면은 mock 데이터 기반 UI 구현
  - 관리자 대시보드/카테고리/Q&A 게시글 화면은 mock 데이터 기반 UI 구현
- 관리자 사용자 관리 화면 구현 완료 (사용자 목록, 상세 정보, 이력서 파싱 데이터 및 파일 프리뷰)
- 사용자/관리자 이력서 화면에서 파싱 데이터(프로필, 이메일, 연락처, 링크, 기술, 학력, 교육, 경력, 프로젝트, 자격증, 자기소개서 목차, 수상, 어학, 원문)를 조회·수정 가능
- 이력서 파싱 데이터 화면은 1/2/3차 프로젝트와 자기소개서 목차를 개별 카드로 분리해 표시
- 루트 `package.json` 편의 스크립트(`dev`, `build`, `lint`)는 실제 Next.js/FastAPI 경로 기준으로 정리됨
- Next.js Turbopack root는 `frontend`로 고정되어 루트 `package-lock.json`이 있어도 alias/라우트 해석이 흔들리지 않음
- 프론트엔드 공통 API 클라이언트가 백엔드 공통 에러 응답 `{ code, message, details }`를 수신하도록 구성됨
- 프론트엔드 계획 스택 반영 완료
  - React 19 적용
  - Next.js 16 App Router 적용
  - Tailwind CSS v4 및 `@tailwindcss/postcss` 적용
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
- 이력서 파서는 현재 “안정화된 파싱” 기준으로 저장됨
  - 프로젝트/포트폴리오와 자기소개서 목차가 섞이지 않도록 큰 섹션과 자기소개서 내부 목차를 분리 처리
  - Gemini LLM 파싱 결과가 프로젝트를 요약/병합하거나 자기소개서 항목을 경력/프로젝트에 섞을 때 후처리로 보정

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

### 이력서 도메인

- `POST /resumes` — 현재 사용자의 이력서 파일 업로드, 원본 저장, 텍스트 추출, 기본 파싱 결과 저장
- `GET /resumes` — 현재 사용자의 이력서 목록 조회
- `GET /resumes/{resume_id}` — 현재 사용자의 이력서 상세 및 파싱 결과 조회
- `GET /resumes/{resume_id}/file` — 이력서 원본 파일 스트리밍 (프리뷰용, 인증 헤더 기반 Blob URL 대응)
- `PATCH /resumes/{resume_id}` — 현재 사용자의 이력서 제목/추출 원문/파싱 JSON 수정
- `DELETE /resumes/{resume_id}` — 현재 사용자의 이력서 소프트 삭제 + 추출 원문/파싱 결과 삭제 + 저장 파일 삭제
- `GET /admin/users` — 관리자 사용자 목록 조회
- `GET /admin/users/{user_id}` — 관리자 사용자 상세 및 해당 사용자의 이력서 목록 조회
- `GET /admin/users/resumes/{resume_id}` — 관리자 이력서 상세 및 파싱 결과 조회
- `PATCH /admin/users/resumes/{resume_id}` — 관리자 이력서 제목/추출 원문/파싱 JSON 수정
- `GET /admin/users/resumes/{resume_id}/file` — 관리자 이력서 원본 파일 스트리밍 (프리뷰용, 파일 미존재 시 404)
- 지원 파일: PDF, DOCX, TXT, 최대 10MB
- 파싱 상태: `PENDING` / `COMPLETED` / `FAILED`
- 파싱 결과: 프로필 후보, 이메일, 전화번호, URL, 기술 키워드, 섹션별 원문(학력/교육/경력/프로젝트/자격증/자기소개서/수상/어학), AI 분석용 하이라이트, 추출 텍스트 길이
- 이력서 테이블은 `created_at`, `created_by`, `created_ip`, `updated_at`, `updated_by`, `updated_ip` 감사 컬럼 포함
- 기본 이력서는 사용자별 1개만 유지되도록 부분 unique index(`uq_resumes_one_default_per_user`) 적용

## 완료된 프론트엔드 기능

- Next.js 16 App Router + React + TypeScript 프로젝트 구성
- Tailwind CSS v4 기반 전역 스타일과 사용자/관리자 레이아웃 구성
- React 19 기반으로 업그레이드
- Next.js 16 및 `@tailwindcss/postcss` 기반 빌드 설정 적용
- ESLint 9 flat config 기반 lint 설정 적용
- Next.js 개발 서버 기본 포트 `3000`을 백엔드 기본 CORS 허용 origin에 추가
- 기존 Vite 개발 포트 `5173/5174` CORS 허용값은 과거 호환용으로 유지
- axios API 클라이언트 구성
  - 기본 API URL: `NEXT_PUBLIC_API_URL` 또는 `http://localhost:8000`
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
- Next.js App Router 사용자 라우트: `/user/dashboard`, `/user/resumes`, `/user/jobs`, `/user/matches`
- Next.js App Router 관리자 라우트: `/admin/dashboard`, `/admin/categories`, `/admin/posts`, `/admin/jobs`
- 관리자 대시보드 `GET /admin/stats` 연결 완료: 전체 사용자·활성 카테고리·총 게시글·오늘 가입·채용공고 수 실데이터 표시, 로딩 스켈레톤·에러 배너 포함
- 관리자 채용공고 화면(`/admin/jobs`) 신설: 소스 탭 필터(전체/ALIO/WORK24/SARAMIN/MANUAL), 상태 배지(OPEN/CLOSED/EXPIRED/HIDDEN), 마스터-디테일 레이아웃, 수집 메타 패널 포함
- 관리자 라우트는 `user.role === 'ADMIN'`일 때만 접근 가능
- 관리자 카테고리 화면 실제 API 연결 + CRUD 모달 (생성·수정·삭제)
- 관리자 Q&A 게시글 화면 실제 API 연결 + CRUD 모달 (생성·수정·삭제, 페이지네이션)
- 사용자 채용공고 화면: ALIO/Mock 소스 탭 + 서버 페이지네이션 추가
- 회원정보 수정 API (`PATCH /auth/me`) 구현 (이름·비밀번호)
- 사용자 대시보드 "프로필 수정" 모달 추가
- 사용자 이력서 화면(`/user/resumes`) 실제 API 연결 완료
  - `GET /resumes`, `GET /resumes/{resume_id}`, `POST /resumes`, `DELETE /resumes/{resume_id}` 연동
  - `GET /resumes/{resume_id}/file` Blob 조회 기반 PDF 파일 미리보기 연동
  - PDF/DOCX/TXT 업로드 UI, 기본 이력서 설정, 파싱 상태/오류 표시
  - 업로드/AI 분석/맞춤 채용공고 준비 3단계 진행 상태 카드 표시
  - 이메일/전화번호/링크/기술 키워드/학력/교육/경력/프로젝트/자격증/자기소개서 목차/수상/어학/추출 텍스트 표시 및 수정
  - 프로젝트 항목과 자기소개서 목차는 한 덩어리 텍스트가 아니라 개별 카드로 분리 표시
- 관리자 사용자 관리 화면(`/admin/users`) 실제 API 연결 완료
  - 사용자 목록 클릭 시 사용자 상세, 이력서 목록, 이력서 파싱 데이터 표시
  - 관리자 전용 이력서 상세/파일 Blob API로 파싱 정보와 PDF 프리뷰 표시
  - 관리자도 사용자 이력서의 파싱 데이터와 추출 원문 수정 가능
  - 1/2/3차 프로젝트 및 자기소개서 목차를 카드 단위로 구분해 가독성 개선
- IT 채용 Mock 화면 추가 (`/user/mock-jobs`, `/admin/mock-jobs`)
  - `MockJobItem` 타입 + 20개 IT 기업 Mock 데이터 (Work24 테이블 구조 기반)
  - 카테고리 필터 탭 (백엔드/프론트엔드/AI·ML/DevOps·SRE/모바일/데이터/QA·보안/게임)
  - 기술스택 칩, 연봉 표시, AI 분석 예정 플레이스홀더
  - 관리자 화면: 테이블 뷰 + 통계 카드 + 카테고리 분포 차트
  - UserLayout, AdminLayout 네비게이션 항목 추가
- `backend/app/schemas/__init__.py` TokenResponse → AuthResponse 수정 (ImportError 해결)
- 이력서 등록 도메인 구현 완료
  - `resumes` 테이블 추가: 원본 파일 메타데이터, 저장 경로, 추출 텍스트, 규칙 기반 파싱 JSON, 파싱 상태, 소프트 삭제, 감사 컬럼 포함
  - `POST /resumes`: PDF/DOCX/TXT 업로드, 최대 용량 초과 시 스트리밍 읽기 중단, 로컬 파일 저장, 기본 텍스트 추출 및 프로필/이메일/전화번호/URL/기술 키워드/주요 섹션 파싱
  - `GET /resumes`, `GET /resumes/{resume_id}`, `DELETE /resumes/{resume_id}` 사용자 본인 이력서 API 추가
  - 이력서 삭제 시 DB 원문/파싱 개인정보를 비우고 저장 파일을 삭제
  - 사용자별 기본 이력서는 DB 부분 unique index로 1개만 허용
  - PDF/DOCX 파싱 의존성으로 `pypdf`, `python-docx` 추가
  - 사용자 직접 수정 API와 관리자 카테고리/Q&A 게시글 CRUD에 `updated_ip` 기록 보강

- `frontend/src/api/admin.ts`
- `frontend/src/app`
- `frontend/src/screens/admin/AdminJobsPage.tsx`
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
- `backend/app/api/resumes.py`
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
- `backend/app/models/resume.py`
- `backend/app/models/user.py`
- `backend/app/repositories/category_repository.py`
- `backend/app/repositories/batch_job_run_repository.py`
- `backend/app/repositories/job_source_repository.py`
- `backend/app/repositories/job_posting_repository.py`
- `backend/app/repositories/post_repository.py`
- `backend/app/repositories/resume_repository.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/schemas/auth.py`
- `backend/app/schemas/category.py`
- `backend/app/schemas/job_collection.py`
- `backend/app/schemas/post.py`
- `backend/app/schemas/resume.py`
- `backend/app/schemas/user.py`
- `backend/app/services/category_service.py`
- `backend/app/services/alio_collection_service.py`
- `backend/app/services/job_source_service.py`
- `backend/app/services/job_posting_service.py`
- `backend/app/services/post_service.py`
- `backend/app/services/resume_parser.py`
- `backend/app/services/resume_service.py`
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
- `backend/alembic/versions/f2a3b4c5d6e7_create_resumes_table.py`
- `backend/.env.example`
- `frontend/package.json`
- `frontend/next.config.ts`
- `frontend/postcss.config.mjs`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/providers.tsx`
- `frontend/src/components/auth/RequireAuth.tsx`
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
- `frontend/src/api/resumes.ts`
- `frontend/src/screens/LoginPage.tsx`
- `frontend/src/screens/SignupPage.tsx`
- `frontend/src/screens/user/ResumesPage.tsx`
- `frontend/src/components/layout/UserLayout.tsx`
- `frontend/src/components/layout/AdminLayout.tsx`
- `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`
- `HANDOFF.md`
- `ai_context/API_SPEC.md`

## 최근 검증

2026-05-06 관리자 이력서 파싱 데이터 가독성 개선:

- `ResumeParsedDataEditor` 표시 개선
  - `projects` 값이 한 문자열에 `1차/2차/3차` 형태로 뭉쳐 있어도 화면에서 프로젝트별 카드로 분리 표시
  - 프로젝트 수정 저장 시에도 분리된 배열 형태로 정리
  - `cover_letter_sections` 또는 자기소개서 원문에 섞인 `지원동기/성장과정/성격의 장단점/입사 후 포부` 등 목차를 개별 카드로 분리 표시
  - 자기소개서 목차 개수를 배지로 표시해 관리자 화면에서 빠르게 스캔 가능
- 검증:
  - `.\.venv\Scripts\python.exe -m compileall app` 통과
  - `npm run lint` 통과
  - `npm run build` 통과 (20개 App Router 경로 생성)

2026-05-06 이력서 파싱 상세 표시 및 수정 기능 추가:

- 백엔드:
  - `ResumeUpdate` 스키마 추가
  - `PATCH /resumes/{resume_id}` 추가: 본인 이력서 제목/추출 원문/파싱 JSON 수정
  - `PATCH /admin/users/resumes/{resume_id}` 추가: 관리자 이력서 제목/추출 원문/파싱 JSON 수정
  - `ResumeRepository.update_resume_content()`, `ResumeService.update_resume_content()`, `update_resume_content_for_admin()` 추가
- 프론트엔드:
  - `ResumeParsedDataEditor` 공통 컴포넌트 추가
  - 사용자 이력서 화면과 관리자 사용자 관리 화면에서 프로필, 이메일, 연락처, 링크, 기술, 학력, 교육/훈련, 경력사항, 프로젝트, 자격증, 자기소개서/목차, 수상, 어학, 추출 원문 표시
  - 사용자와 관리자 모두 편집 모드에서 파싱 데이터와 원문을 수정해 저장 가능
- 검증:
  - `.\.venv\Scripts\python.exe -m compileall app` 통과
  - `npm run lint` 통과
  - `npm run build` 통과 (20개 App Router 경로 생성)
  - FastAPI route 확인: `PATCH /resumes/{resume_id}`, `PATCH /admin/users/resumes/{resume_id}` 등록 확인

2026-05-06 이력서 프리뷰/관리자 사용자 화면 빌드 오류 수정:

- `frontend/src/app/admin/users/page.tsx`: 기존 프로젝트 패턴에 맞게 `@/` alias import를 상대 경로 import로 수정
- `frontend/next.config.ts`: Turbopack root를 `frontend` 실행 디렉터리로 고정해 루트 `package-lock.json` 때문에 workspace root가 잘못 잡히던 문제 해결
- 루트 `package.json`: `dev:backend`를 `uvicorn app.main:app` 기준으로 수정하고 루트 `build`/`lint` 편의 스크립트 추가
- `.gitignore`: 루트 `node_modules/` ignore 추가
- `frontend/src/screens/user/ResumesPage.tsx`, `frontend/src/screens/admin/AdminUsersPage.tsx`: PDF 프리뷰 Blob 로딩을 TanStack Query 기반으로 정리하고 object URL revoke 처리
- `backend/app/api/admin_users.py`: 관리자 이력서 파일 프리뷰 요청 시 실제 파일이 없으면 404로 응답하도록 보강
- 검증:
  - `.\.venv\Scripts\python.exe -m compileall app` 통과
  - `npm run lint` 통과 (`frontend`, 루트 스크립트 모두 확인)
  - `npm run build` 통과 (`frontend`, 루트 스크립트 모두 확인, 20개 App Router 경로 생성)
  - `.\.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"` 통과 (`jobfit-ai`)

2026-05-06 이력서 PDF 프리뷰 500 에러 수정 및 안정화:

- 백엔드: `GET /resumes/{id}/file` API에 파일 존재 여부 체크 로직 추가 및 `Path` 참조 오류 수정
- 프론트엔드: `iframe`의 `src`에 직접 URL을 넣는 방식에서 `axios`로 Blob 데이터를 받아 `URL.createObjectURL`을 사용하는 방식으로 변경
  - 브라우저가 `iframe` 요청 시 인증 쿠키를 누락하거나 CORS 정책으로 차단되는 문제 해결
  - PDF 로딩 상태 표시(스켈레톤/스피너) 및 에러 처리 UI 보강
- 관리자 페이지: `AdminUsersPage`에도 동일한 Blob URL 방식 프리뷰 적용 및 `adminApi`에 `getResumeFileBlob` 추가
- 검증:
  - `python -m compileall app` 통과
  - 사용자 페이지 이력서 PDF 프리뷰 정상 출력 확인 (Blob URL 생성 확인)
  - 관리자 페이지 사용자별 이력서 PDF 프리뷰 정상 출력 확인
  - 존재하지 않는 파일 요청 시 백엔드에서 404 에러 코드로 응답 확인

2026-05-06 이력서 PDF 프리뷰 및 관리자 사용자 관리 기능 고도화:

2026-05-06 이력서 업로드 진행 UI 및 취약점 점검:

- `frontend/src/screens/user/ResumesPage.tsx`
  - 이력서 업로드 중 `이력서 업로드 → AI 분석 → 맞춤 채용공고` 3단계 진행 카드 추가
  - 진행률 바, 단계 스테퍼, 파일명/용량 표시, 분석 완료/실패 상태 표시 추가
  - 프론트엔드 파일 확장자 및 10MB 용량 사전 검증 추가
- 의존성 보안 업데이트
  - `pypdf` `6.4.1 → 6.10.2`
  - `pdfplumber` `0.11.4 → 0.11.9` (`pdfminer-six==20251230` 호환)
- 검증
  - `python -m compileall app` 통과
  - `pip-audit -r requirements.txt` 통과: 알려진 취약점 없음
  - `npm audit --audit-level=moderate` 통과: 취약점 0건
  - `npm run lint` 통과
  - `npm run build` 통과 (19개 라우트)
  - `git diff --check` 통과 (CRLF 경고만 출력)

2026-05-06 이력서 파서 개선 — 프로젝트 전체 표시 + 자기소개서 목차 구조화:

- `resume_parser.py` 버그 수정 및 기능 추가
  - `_classify_section_header`: `startswith` 매칭 강화 — "프로젝트 1차: 쇼핑몰" 같은 본문 제목 라인이 섹션 헤더로 오인식되어 누락되던 문제 수정
  - `_detect_sections`: 자기소개서 소제목("성장과정", "지원동기", "성격의 장단점", "입사 후 포부")을 섹션 헤더로 처리하면서도 텍스트 내용에 포함 — `_parse_cover_letter_sections`가 구조화 시 활용
  - `_group_section_items()` 신설: 빈 줄 구분자로 프로젝트 섹션을 개별 항목 블록으로 그룹화 (1차/2차/3차 분리)
  - `_parse_cover_letter_sections()` 신설: 자기소개서 텍스트를 소제목별로 분리해 `dict[str, str]` 반환
  - `_match_cover_letter_subsection()` 신설: 소제목 매칭 헬퍼
  - `COVER_LETTER_SECTION_LABELS`, `_COVER_LETTER_SUBSECTION_COMPACT` 상수 추가
  - `parse_resume_text()`: `projects`를 `_group_section_items` 기반 블록 리스트로, `cover_letter_sections` 필드 추가
  - `parse_resume_with_llm()`: `cover_letter_sections` 필드 추가 (LLM 결과도 소제목 파싱 적용)
  - `parse_resume_with_llm()`: Gemini 입력 제한을 8,000자에서 20,000자로 확대하고, 규칙 기반 프로젝트 후보를 프롬프트에 함께 전달
  - LLM이 프로젝트를 요약/병합해 후보보다 적게 반환하면 규칙 기반 프로젝트 항목을 보존하도록 보정
  - 제어문자(`\x00` 계열, `` 등)와 zero-width 문자를 제거하는 공통 정규화 함수 추가
  - DOCX 파싱 시 `document.paragraphs`뿐 아니라 `document.tables`의 셀 텍스트도 함께 추출
  - `포트폴리오`, `작업물`, `portfolio`를 프로젝트 계열 섹션으로 인식하도록 추가
  - 자기소개서 목차 인식 확장: `지원동기 및 입사 후 포부`, `기술역량 및 프로젝트`, 직무역량, 성장배경, 학교생활, 가치관, 생활신조, 문제해결/협업/도전/성취/실패/갈등해결/리더십 경험 등 흔한 소제목 변형 추가
  - 번호/불릿이 붙은 자기소개서 소제목(`1. 지원동기`, `가. 가치관` 등)도 같은 목차로 인식하도록 보강
  - 자기소개서 소제목을 `SECTION_ALIASES`의 큰 섹션 판별 목록에서는 제외하고, 자기소개서 내부 목차 전환/분리에만 사용하도록 수정
  - `기술역량 및 프로젝트`, `프로젝트 후기`처럼 자기소개서/포트폴리오 양쪽에서 쓰이는 애매한 제목은 명시적 자기소개서 내부에서만 자기소개서 목차로 처리
  - LLM 결과의 `experiences`/`projects`에 자기소개서 목차(`기술역량 및 프로젝트`, `프로젝트 후기` 등)가 섞이면 후처리에서 제거
  - 모듈 주석 `ANTHROPIC_API_KEY` → `GEMINI_API_KEY` 수정
  - `_normalize_pdf_text` 중복 "# 3." 주석 수정
- `frontend/src/api/types.ts`: `ResumeParsedData`에 `cover_letter_sections?: Record<string, string>` 추가
- `frontend/src/screens/user/ResumesPage.tsx`:
  - `TextListBlock`: `slice(0, 8)` 제한 제거, `whitespace-pre-wrap` 추가
  - `ProjectsBlock` 신설: 각 프로젝트를 별도 카드로 표시 (1차/2차/3차 모두 표시)
  - `CoverLetterSectionsBlock` 신설: 소제목별 자기소개서 목차 표시
  - `StructuredParsedData`: 위 두 컴포넌트 적용, 자기소개서 섹션 분리 표시
- `python -m compileall app/services/resume_parser.py` 통과
- `python -m compileall app` 통과
- 샘플 검증: `1차/2차/3차` 프로젝트 텍스트가 `projects` 3개 항목으로 분리됨 확인
- 샘플 검증: `지원동기 및 입사 후 포부`, `기술역량 및 프로젝트`, `가. 가치관` 자기소개서 목차가 `cover_letter_sections`로 분리됨 확인
- 샘플 검증: `경력` 뒤에 `기술역량 및 프로젝트`, `프로젝트 후기`가 이어져도 경력에는 회사/기간만 남고 해당 내용은 자기소개서 목차로 분리됨 확인
- 샘플 검증: `자기소개서` 뒤 `포트폴리오`가 나오면 자기소개서와 프로젝트가 섞이지 않고 각각 `cover_letter_sections`, `projects`로 분리됨 확인
- 2026-05-06 기준 안정화된 파싱 버전으로 저장 및 GitHub 푸시 예정
- `npm run lint` 통과 (경고 0개)
- `npm run build` 통과 (19개 라우트)

2026-05-04 내 정보·결제·관리자 구분 구현:

- `DELETE /auth/me` 계정 탈퇴 엔드포인트 추가
  - `UserRepository.soft_delete()`: is_deleted=True, updated_by/ip 갱신
  - `UserService.delete_me()`: 모든 RefreshToken revoke 후 소프트 삭제
  - 탈퇴 후 Access/Refresh Token 쿠키 자동 삭제
- 프론트엔드 `/user/profile` 내 정보 페이지 추가
  - 기본 정보(이름 수정), 비밀번호 변경, 계정 탈퇴 3개 탭
  - 계정 탈퇴는 "탈퇴합니다" 입력 확인 모달 포함
  - `authApi.deleteMe()` 연결, 탈퇴 후 /login 리다이렉트
- 프론트엔드 `/user/payment` 결제 페이지 추가
  - Free/Pro/Enterprise 3개 플랜 카드 UI
  - 월간/연간 토글 (연간 20% 할인)
  - 카드 결제 폼 (mock — 실제 PG 미연동)
  - 결제 완료 성공 화면
- `UserLayout` 네비게이션에 "내 정보"(/user/profile), "요금제"(/user/payment) 추가
  - "IT 채용 (Mock)" 항목 제거 (Admin 전용)
- `AdminLayout` 관리자 구분 강화
  - 사이드바: 진한 네이비(#0f172a) 배경으로 사용자 영역과 명확히 구분
  - 상단 ADMIN 빨간 배지, 네이바 섹션 레이블 추가
  - 탑바: 좌측 빨간 보더 + "ADMIN MODE" 점멸 표시
  - 사이드바 하단 "사용자 화면으로" 링크 추가
- `Icon.tsx`에 `credit-card`, `shield`, `trash` 아이콘 추가
- `python -m compileall app` 통과 (에러 없음)
- `npm run build` 통과 (19개 라우트: /user/profile, /user/payment 포함)

2026-05-04 이력서 등록 API + 기본 파싱 + 감사 IP 보강:

- `AuditMixin` 기준 대부분의 주요 테이블은 이미 `created_at`, `created_by`, `created_ip`, `updated_at`, `updated_by`, `updated_ip` 감사 컬럼을 갖고 있음을 확인
- 신규 `resumes` 테이블도 동일 감사 컬럼과 `is_deleted` 소프트 삭제 컬럼 포함
- `POST /resumes`, `GET /resumes`, `GET /resumes/{resume_id}`, `DELETE /resumes/{resume_id}` 구현
- 이력서 파일은 `settings.resume_upload_dir` 하위에 사용자별 디렉터리로 저장, 기본 최대 10MB
- 업로드 파일은 최대 용량을 넘으면 전체 파일을 메모리에 올리기 전에 읽기를 중단
- DB 저장 실패 시 방금 저장한 이력서 파일을 정리하도록 보강
- 이력서 삭제 시 소프트 삭제와 함께 원문 텍스트/파싱 JSON/파일 메타 개인정보를 비우고 실제 저장 파일 삭제
- 사용자별 기본 이력서 1개 보장을 위한 `a1b2c3d4e5f6_add_resume_default_unique_index.py` 마이그레이션 추가
- TXT는 즉시 텍스트 추출 가능, PDF/DOCX는 `pypdf`, `python-docx` 의존성 기반 추출
- 파싱 결과는 프로필 후보, 이메일, 전화번호, URL, 기술 키워드, 섹션별 원문, AI 분석용 하이라이트, 추출 텍스트 길이를 `parsed_data` JSON에 저장
- 회원정보 수정, 관리자 카테고리 CRUD, 관리자 Q&A 게시글 CRUD에 `updated_ip` 기록 보강
- 프론트엔드 `/user/resumes` 화면을 실제 이력서 API와 연결하고 mock 업로드 흐름 제거
- `python -m compileall app` 통과
- `pip install pypdf==6.4.1 python-docx==1.2.0` 통과
- `alembic heads` 결과 `a1b2c3d4e5f6 (head)` 확인
- `alembic upgrade head` 통과 (`f2a3b4c5d6e7 → a1b2c3d4e5f6`)
- FastAPI TestClient 검증: 회원가입 201, TXT 이력서 업로드 201 + `parse_status=COMPLETED`, `GET /resumes` 200 + 1건
- FastAPI TestClient 검증: DOCX 이력서 업로드 201 + `parse_status=COMPLETED`, 기술 키워드 파싱 확인
- FastAPI TestClient 검증: 기본 이력서 2회 업로드 시 기본값 1개 유지, `DELETE /resumes/{resume_id}` 후 저장 파일 삭제 및 DB 원문/파싱 데이터 제거 확인
- PDF 텍스트 추출 시 `J A V A`, `0 1 0 - ...`처럼 문자 사이 공백이 삽입되는 케이스를 보정해 기술 키워드/전화번호/이메일 파싱 개선
- 프로토콜 없는 `github.com/...` 계열 URL과 PDF에서 벌어진 URL 후보를 인식하도록 URL 파싱 보강
- AI 분석 입력을 위해 학력/교육/경력/프로젝트/자격증/자기소개서/수상/어학 섹션 감지 및 하이라이트 추출 추가
- 기존 업로드 이력서에 `raw_text`는 있으나 파싱 결과가 비어 있으면 상세 조회 시 `parsed_data`를 재계산해 저장하도록 보강
- 파서 샘플 검증: 분리된 이메일, 전화번호, `github.com/...`, `J A V A`, `Spring Boot`, 학력/교육/경력/프로젝트/자격증/자기소개서 섹션 추출 확인
- `npm run lint` 통과
- `npm run build` 통과 (Next.js 16.2.4, 17개 정적 경로)
- `git diff --check` 통과 (CRLF 경고만 출력)

2026-05-04 JWT 토큰 쿠키 저장 + Refresh Token DB 영속화 (현업 방식 적용):

- **Access Token**: localStorage 제거 → HttpOnly 쿠키(`access_token`, 15분, `SameSite=Lax`, `path=/`)
- **Refresh Token**: HttpOnly 쿠키(`refresh_token`, 14일) + DB `refresh_tokens` 테이블에 SHA-256 해시 저장
- `backend/app/models/refresh_token.py` 신설: `id`, `user_id`, `token_hash`, `family_id`, `is_revoked`, `expires_at`, `created_ip`, `created_at`
- `backend/app/repositories/refresh_token_repository.py` 신설: `create`, `get_by_hash`, `get_active_by_hash`, `revoke`, `revoke_family`, `revoke_all_by_user`
- `backend/app/core/security.py`: `hash_token()` (hashlib.sha256) 추가
- `backend/app/core/config.py`: `access_token_cookie_name/secure/samesite` 설정 추가
- `backend/app/services/user_service.py`:
  - `create_token_pair(user, ip)`: Refresh Token DB 저장
  - `refresh(token, ip)`: JWT 검증 → DB 해시 조회 → 취소 토큰 재제출 시 family 전체 취소(재사용 공격 대응) → 로테이션
  - `logout(token)`: DB에서 해당 토큰 취소
  - `update_me()`: 비밀번호 변경 시 `revoke_all_by_user()` 호출 (전체 세션 강제 만료)
- `backend/app/schemas/auth.py`: `TokenResponse` 폐기 → `AuthResponse { user }` (응답 바디에 토큰 미포함)
- `backend/app/api/auth.py`: `_set_token_cookies()` 두 토큰 동시 쿠키 설정, `logout` DB 취소 추가
- `backend/app/api/deps.py`: `HTTPBearer` 제거 → `request.cookies.get(access_token_cookie_name)` 방식으로 전환
- Alembic 마이그레이션 `e1f2a3b4c5d6_add_refresh_tokens_table.py` 생성 및 `upgrade head` 적용
- `frontend/src/api/client.ts`: Authorization 헤더 주입 제거, 401 자동 Refresh 인터셉터 추가 (pendingQueue로 동시 401 처리)
- `frontend/src/stores/authContext.ts`: `token` 필드 제거, `login(user)` 시그니처 변경
- `frontend/src/stores/authStore.tsx`: localStorage 완전 제거, 앱 시작 시 `/auth/me` → 실패 시 `/auth/refresh` 순으로 세션 복원
- `frontend/src/api/types.ts`: `AuthTokenResponse` 폐기 → `AuthResponse { user }` 로 교체
- `.gitignore`: 루트에 `frontend/.next/`, `*.tsbuildinfo` 추가, `frontend/.gitignore` Vite 잔재 제거 및 Next.js 패턴으로 정리
- `python -m compileall app` 통과
- `alembic upgrade head` 통과 (`b8050fd5e470 → e1f2a3b4c5d6`)
- `npm run lint` 통과 (경고 0개)
- `npm run build` 통과 (15개 라우트)

2026-05-04 `'use client'` 명시 추가:

- Next.js App Router 베스트 프랙티스 적용: hooks/navigation API를 사용하는 모든 컴포넌트에 `'use client'` 지시문 명시
- 추가 대상: `screens/LoginPage`, `screens/SignupPage`, `screens/user/DashboardPage`, `screens/user/JobsPage`, `screens/user/MatchesPage`, `screens/user/ResumesPage`, `screens/admin/AdminDashboardPage`, `screens/admin/AdminJobsPage`, `screens/admin/CategoriesPage`, `screens/admin/PostsPage`, `components/layout/UserLayout`, `components/layout/AdminLayout` (12개 파일)
- `npm run lint` 통과 (경고 0개)
- `npm run build` 통과 (Next.js 16.2.4, 15개 라우트 정적 생성)

2026-05-04 프론트엔드 Next.js 전환:

- 전환 전 기준점 확인: 기존 프론트엔드는 `package.json` 기준 Vite 8 + React Router v7 + `VITE_API_URL` 구조였고, `HANDOFF.md`와 `git status --short` 확인 후 작업 시작
- 프론트엔드 빌드 도구를 Vite에서 Next.js 16 App Router로 전환
  - `next`, `@tailwindcss/postcss`, `postcss.config.mjs`, `next.config.ts`, `next-env.d.ts` 추가
  - `vite`, `@vitejs/plugin-react`, `@tailwindcss/vite`, `react-router-dom`, Vite 엔트리 파일 제거
  - 기존 `src/pages` 화면 컴포넌트는 Next Pages Router 충돌을 피하기 위해 `src/screens`로 이동
  - `src/app`에 `/`, `/login`, `/signup`, `/user/*`, `/admin/*` App Router 경로 추가
- React Router 의존 제거
  - `Link`, `useRouter`, `usePathname`을 Next.js API로 교체
  - `UserLayout`, `AdminLayout`은 `children` 기반 App Router 레이아웃으로 변경
  - `RequireAuth`, `RootRedirect` 클라이언트 보호 라우트 컴포넌트 추가
- 프론트엔드 API 환경 변수명을 `VITE_API_URL`에서 `NEXT_PUBLIC_API_URL`로 변경
- Next.js SSR/프리렌더링 대응
  - `AuthProvider`와 `AuthContext`를 client component로 명시
  - `localStorage` 초기 접근을 클라이언트 마운트 이후로 이동
  - axios interceptor에 `typeof window` 가드 추가
- 백엔드 기본 CORS origin에 Next.js 개발 서버 포트 `localhost/127.0.0.1:3000` 추가
- npm audit에서 Next 내부 `postcss` 하위 의존성 취약점이 보고되어 `overrides.postcss=^8.5.10`으로 보정
- 검증 결과
  - `npm run lint` 통과
  - `npm run build` 통과 (Next.js 16.2.4, App Router 14개 경로 + `_not-found` 정적 생성)
  - `npm audit --audit-level=moderate` 통과 (취약점 0개)
  - `python -m compileall app` 통과
  - `git diff --check` 통과 (공백 오류 없음)
  - Next.js dev server `http://127.0.0.1:3000` 기동 및 HTTP 200 응답 확인

2026-04-30 관리자 화면 API 연결·회원 수정 API·채용공고 UX 개선:

- `alembic upgrade head` 실행 완료 (data_source 마이그레이션 `b8050fd5e470` 적용)
- `backend/data/mock_work24_jobs.json` 생성 (IT 기업 10개 공고 — 카카오·네이버·라인·쿠팡·토스 등)
- 관리자 카테고리 화면(`/admin/categories`) 실제 API 연결 + CRUD 모달 구현
  - 카테고리 생성·수정(slug 자동완성 포함)·삭제(확인 다이얼로그) 동작
  - TanStack Query `invalidateQueries` 기반 즉시 갱신
- 관리자 Q&A 게시글 화면(`/admin/posts`) 실제 API 연결 + CRUD 모달 구현
  - 카테고리 드롭다운 동적 조회, 게시글 생성·수정·삭제 구현
  - 카테고리/offset 기반 서버 페이지네이션 적용 (limit=20)
- 사용자 채용공고 화면(`/user/jobs`) 개선
  - 소스 탭 추가: 공공기관(ALIO·data_source=PRODUCTION) / IT 기업(data_source=MOCK)
  - 서버 페이지네이션 추가 (PAGE_SIZE=20, 탭·페이지 변경 시 selected 초기화)
- 회원정보 수정 백엔드 API 구현
  - `UserUpdate` 스키마 추가 (이름, 현재/새 비밀번호 선택적)
  - `UserRepository.update()`, `UserService.update_me()`, `InvalidCurrentPasswordError` 추가
  - `PATCH /auth/me` 엔드포인트 추가 (현재 비밀번호 틀리면 400 `AUTH_004`)
- 회원정보 수정 프론트엔드 구현
  - `authApi.updateMe()` 추가, `AuthContext.setUser()` 추가
  - 사용자 대시보드 우상단 "프로필 수정" 버튼 → 이름·비밀번호 변경 모달
- `frontend/src/api/jobs.ts` `GetJobsParams`에 `data_source` 파라미터 추가
- `frontend/src/api/admin.ts` 카테고리·게시글 CRUD API 메서드 추가
- `frontend/src/api/types.ts` Category·Post 관련 타입 추가
- `python -m compileall app` 통과
- `npm run lint` 통과 (경고 0개)
- `npm run build` 통과 (232 modules)

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

- 현재 프론트엔드 구현 스택은 `package.json` 기준 Next.js 16, React 19, Tailwind CSS v4이다.
- Next.js 개발 서버 기본 포트는 `3000`이다.
- TanStack Query, React Hook Form, Zod, shadcn/ui 패턴 기반 공통 컴포넌트는 적용 완료.
- 로컬 Node 버전은 `v20.20.2`로 확인되었고, Tailwind CSS v4 native binding 이슈 없이 빌드가 통과한다.
- 백엔드 CORS 기본값과 `.env.example`은 Next.js 기본 포트 `3000`과 기존 Vite 포트 `5173/5174`를 모두 포함한다.

## 다음 작업

### 🔴 우선순위 높음
1. **Claude API 연동** — `POST /ai/analyze` 이력서 vs 공고 강점·약점·개선 제안 분석
2. **벡터 임베딩** — sentence-transformers + pgvector 매칭 점수 계산
3. 이력서 파싱 재시도 API/관리자 파싱 실패 모니터링 범위 결정
4. **결제 PG 연동** — 현재 결제 페이지는 mock UI만 구현, 실제 PG(토스페이먼츠 등) 연동 필요
5. **이력서 파서 개선** — DOCX 테이블 내용 추출, AI 입력용 `format_resume_for_ai()` 함수 추가

### 🟡 우선순위 중간
4. PDF/DOCX 실제 샘플 업로드 검증 (`pypdf`, `python-docx` 설치 후)
5. **프론트엔드 AI 매칭 화면** (`/user/matches`) — 매칭 점수 게이지, 강점/약점, AI 개선 제안
6. `POST /admin/jobs/sources/mock/load` Swagger 테스트 (mock_work24_jobs.json DB 로드 확인)
7. DB 확인: `SELECT data_source, COUNT(*) FROM job_postings GROUP BY data_source;`

### 🟢 우선순위 낮음
8. **지원 현황 화면** (`/user/applications`) — Kanban/리스트 뷰, localStorage 기반
9. ALIO 코드 동기화 배치 (`ALIO_CODE_SYNC`) 구현 여부 결정
10. Docker Compose 전체 통합 (프론트 + 백엔드 + DB)

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
