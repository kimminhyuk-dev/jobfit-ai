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
- 프론트엔드: React 19, TypeScript, Vite, Tailwind CSS 3 기반 초기 구현 완료
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
- 프론트엔드 계획 스택 일부 반영 완료
  - React 19 적용
  - TanStack Query Provider 적용
  - React Hook Form + Zod 기반 로그인/회원가입 폼 검증 적용
  - shadcn/ui 방식의 `Button`, `Input`, `Alert` 공통 컴포넌트 추가
- 루트 AI 에이전트 지시 문서 생성 완료 (AGENTS.md / CLAUDE.md / GEMINI.md)
- AI 인수인계 문서는 루트 `HANDOFF.md`로 단일화 완료

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

## 완료된 프론트엔드 기능

- Vite + React + TypeScript 프로젝트 구성
- Tailwind CSS 기반 전역 스타일과 사용자/관리자 레이아웃 구성
- React 19 기반으로 업그레이드
- axios API 클라이언트 구성
  - 기본 API URL: `VITE_API_URL` 또는 `http://localhost:8000`
  - `withCredentials: true`로 Refresh Token Cookie 포함
  - Access Token을 `Authorization: Bearer` 헤더에 자동 주입
- TanStack Query `QueryClientProvider` 구성
- 로그인/회원가입 화면 구현 및 `/auth/login`, `/auth/signup`, `/auth/me`, `/auth/logout` 연결
- 로그인/회원가입 화면은 React Hook Form + Zod로 클라이언트 검증 처리
- 공통 에러 응답 타입과 회원가입 validation `details` 필드 매핑 정리
- shadcn/ui 패턴 기반 공통 UI 컴포넌트 추가 (`Button`, `Input`, `Alert`)
- 사용자 라우트: `/user/dashboard`, `/user/resumes`, `/user/jobs`, `/user/matches`
- 관리자 라우트: `/admin/dashboard`, `/admin/categories`, `/admin/posts`
- 관리자 라우트는 `user.role === 'ADMIN'`일 때만 접근 가능

## 주요 파일

- `backend/app/main.py`
- `backend/app/api/auth.py`
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
- `backend/app/models/category.py`
- `backend/app/models/post.py`
- `backend/app/models/user.py`
- `backend/app/repositories/category_repository.py`
- `backend/app/repositories/post_repository.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/schemas/auth.py`
- `backend/app/schemas/category.py`
- `backend/app/schemas/post.py`
- `backend/app/schemas/user.py`
- `backend/app/services/category_service.py`
- `backend/app/services/post_service.py`
- `backend/app/services/user_service.py`
- `backend/alembic/versions/4f6a7b8c9d10_add_categories_and_admin_role.py`
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
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/SignupPage.tsx`
- `frontend/src/components/layout/UserLayout.tsx`
- `frontend/src/components/layout/AdminLayout.tsx`
- `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`
- `HANDOFF.md`
- `ai_context/API_SPEC.md`

## 최근 검증

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

- 현재 프론트엔드 구현 스택은 `package.json` 기준 React 19, Vite 4, Tailwind CSS 3이다.
- TanStack Query, React Hook Form, Zod, shadcn/ui 패턴 기반 공통 컴포넌트는 적용 완료.
- Tailwind CSS v4는 현재 로컬 Node v16.20.2에서 `@tailwindcss/oxide` native binding 문제로 빌드가 깨져 적용하지 않았다.
- Tailwind CSS v4 전환은 Node 20 이상으로 업그레이드한 뒤 재시도한다.

## 다음 작업

1. Node 20 이상으로 업그레이드 후 Tailwind CSS v4 전환 재시도
2. 관리자 카테고리 화면을 실제 `/categories` API와 연결
3. 관리자 Q&A 게시글 화면을 실제 `/posts` API와 연결
4. 사용자용 Q&A 목록·상세 화면 추가 여부 결정
5. 프론트엔드 toast/field error 표시 방식 고도화

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
