# HANDOFF

이 문서는 ChatGPT, Claude, Claude Code 등 다른 AI에게 프로젝트 상태를 한 번에 전달하기 위한 최신 브리핑 문서다.

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
- 프론트엔드: React, TypeScript, Vite 기반 예정
- 인증 방식: JWT Access Token + HttpOnly Refresh Token Cookie
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
- 루트 AI 에이전트 지시 문서 생성 완료 (AGENTS.md / CLAUDE.md / GEMINI.md)

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

## 주요 파일

- `backend/app/main.py`
- `backend/app/api/auth.py`
- `backend/app/api/deps.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/core/security.py`
- `backend/app/models/base.py`
- `backend/app/models/user.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/schemas/auth.py`
- `backend/app/schemas/user.py`
- `backend/app/services/user_service.py`
- `backend/alembic/versions/8dad372a1f24_create_users_table.py`
- `backend/.env.example`
- `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`
- `ai_context/API_SPEC.md`
- `ai_context/HANDOFF.md`

## 최근 검증

2026-04-29 기준 확인 완료:

- `python -m compileall app` 통과
- 인증 라우트 전체 확인 완료 (`/auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`)
- Alembic current: `8dad372a1f24 (head)`
- bcrypt 해시·검증, Access Token 생성·검증 정상
- 실제 DB 세션 기반 인증 흐름 검증 완료 (회원가입 → 로그인 → 토큰 재발급 → 로그아웃)

## 참고 사항

- 백그라운드 dev server 실행은 현재 도구 환경에서 프로세스가 바로 종료되어 유지되지 않는다.
- 포그라운드 실행은 정상 확인됨.
- 서버 실행 명령:

```powershell
cd C:\Users\USER\jobfit-ai\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 다음 작업

1. 인증 API를 실제 서버에서 수동 테스트
2. 회원정보 수정 API 구현
3. 게시글 도메인 모델 설계
4. 게시글 CRUD API 구현
5. 게시글 페이징 / 검색 구현
6. 프론트엔드 로그인 화면 연결

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
