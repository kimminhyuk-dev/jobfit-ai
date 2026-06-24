# JobFit AI

AI 기반 이력서·채용공고 매칭 데모/포트폴리오 플랫폼입니다. `USER`, `COMPANY`, `ADMIN`
세 역할로 구성되어, 이력서 관리부터 공고 탐색·지원·면접 연습까지 엔드투엔드 흐름을 보여줍니다.

## 주요 기능 (구현됨)

- **인증**: 회원가입, 로그인, 토큰 리프레시, 로그아웃, 현재 사용자 조회, 프로필 수정, 회원 탈퇴.
  로그인 포털 분리 — `/login`은 USER 전용, `/company/login`은 COMPANY·ADMIN(이메일 또는 사업자번호 10자리).
- **계정 복구**: 이메일(아이디) 찾기, 비밀번호 재설정 (개인·기업 각각).
- **이력서**: 업로드 및 파싱(PDF/DOCX 텍스트 추출 + Gemini 구조화), 구조화된 프로젝트·자기소개서 섹션 관리.
- **면접 연습 (OpenAI)**: 파싱된 이력서로 세션 생성 시 5문항을 1회 생성·저장하고, 답변을 한 건씩 평가.
  세션 조회는 OpenAI를 호출하지 않으며, 참고 자료는 서버 측 레퍼런스만 사용.
- **채용공고**: 목록/상세/필터(출처·키워드·지역·학력·고용형태·NCS 분류 등)와 페이지네이션.
- **지원 흐름**: 선택한 이력서를 공고에 지원, 동일 `(user_id, job_id)` 활성 중복 지원 차단, 지원 내역 조회·취소.
- **매칭 점수**: 지원 시 이력서와 공고를 **키워드/토큰 기반**으로 비교해 점수와 근거를 산출·저장
  (`local-match-v1`, 알고리즘 버전 `1.0.0`). 임베딩 기반이 아닌 로컬 v1 방식입니다.
- **면접 메일**: 회사가 지원자에게 면접 안내 메일을 발송(SMTP)하고, 지도 이미지를 첨부(Google Maps Static).
- **회사**: 받은 지원 대시보드, 지원자 이력서 조회·상태 변경, 공고 등록·수정·삭제.
- **게시판**: 카테고리·Q&A 게시글(생성/수정/삭제는 ADMIN 전용).
- **RBAC**: 역할(roles)·권한(permissions)·사용자-역할(user_roles)과 `require_permission` 기반 권한 판정.
- **휴가 결재**: RBAC 기반 신청/결재선/직무 분리/잔여 관리.
- **관리자**: 통계, 사용자 관리, 역할 부여·회수, 감사 로그, 공통코드, 동적 메뉴, 채용공고 관리.

## 기술 스택 (확인된 버전)

### Backend — `backend/requirements.txt` (핀된 버전)

| 영역 | 스택 |
|---|---|
| 언어/프레임워크 | Python, FastAPI 0.136.0, Starlette 1.0.0 |
| ORM/마이그레이션 | SQLAlchemy 2.0.49, Alembic 1.18.4 |
| 검증/설정 | Pydantic 2.13.3, pydantic-settings 2.14.0 |
| 서버 | Uvicorn 0.46.0 |
| DB 드라이버 | psycopg 3.3.3 |
| 인증 | python-jose 3.5.0, passlib 1.7.4, bcrypt 4.0.1 |
| 이력서 파일 처리 | pdfplumber 0.11.9, pypdf 6.10.2, python-docx 1.2.0 |
| AI SDK | openai 2.41.0, google-generativeai 0.8.5 |

### Frontend — `frontend/package.json` / `package-lock.json` (설치 버전)

| 영역 | 스택 |
|---|---|
| 프레임워크 | Next.js 16 (App Router), React 19 |
| 언어 | TypeScript 6 |
| 스타일 | Tailwind CSS 4 |
| 상태/폼 | TanStack Query 5, React Hook Form 7, Zod 4 |
| HTTP/아이콘 | axios 1, lucide-react 1 |

### Database / Infra

- PostgreSQL 16 (`postgres:16-alpine`), Docker Compose.

### LLM (용도별 모델 분리)

| 용도 | 모델 | 비고 |
|---|---|---|
| 면접 질문 생성·평가 | OpenAI `gpt-5-mini` | reasoning effort `low`, 최대 출력 토큰 6000 |
| 이력서 파싱·구조화 | Google Gemini | `gemini-2.5-flash-lite` → `gemini-2.0-flash-lite` → `gemini-2.5-flash` 폴백 체인 |

## 아키텍처 개요

백엔드는 계층 흐름을 따릅니다.

```text
api (router) -> service -> repository -> model
```

- `api/`: 요청 수신과 응답 반환만 — 비즈니스 로직 없음.
- `services/`: 비즈니스 로직. 리포지토리 메서드가 있으면 직접 DB 쿼리하지 않음.
- `repositories/`: DB 접근 전용.
- `models/`(SQLAlchemy ORM)와 `schemas/`(Pydantic DTO)는 분리.
- `core/`: config, database/session, security, errors.

### 인증

- Access Token: JWT, 15분, 쿠키 기반 클라이언트 흐름.
- Refresh Token: JWT, 14일, HttpOnly 쿠키, DB에 SHA-256 해시 저장.
- 역할: `users.role`은 `USER`/`COMPANY`/`ADMIN`, `users.admin_level`은 `A`/`B`/`C`(nullable).
- RBAC: `roles`·`permissions`·`user_roles` 테이블과 `require_permission` 의존성으로 기능 권한을 판정.

## 프로젝트 구조

```text
jobfit-ai/
├── backend/
│   └── app/
│       ├── api/            # FastAPI 라우터 (요청/응답만)
│       ├── services/       # 비즈니스 로직
│       ├── repositories/   # DB 접근
│       ├── models/         # SQLAlchemy ORM
│       ├── schemas/        # Pydantic DTO
│       ├── core/           # config, database, security, errors
│       ├── prompts/        # 서버 측 AI 프롬프트·레퍼런스
│       └── scripts/        # 데모 시드/목 데이터 생성
├── frontend/
│   └── src/
│       ├── app/            # Next.js App Router 라우트
│       ├── screens/        # 페이지 단위 UI
│       ├── components/     # 공용 컴포넌트
│       ├── api/            # API 클라이언트·타입
│       └── stores/         # 클라이언트 상태
└── docker-compose.yml
```

## 실행 방법

Backend:

```powershell
docker-compose up -d db
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

루트 헬퍼 스크립트(레포 루트에서 두 앱을 함께 실행):

```powershell
npm run dev     # backend + frontend 동시 실행
npm run lint    # frontend lint
npm run build   # frontend build
```

## 검증

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app

cd ..\frontend
npm run lint
npm run build
```

## 버전 & 로드맵

- **v1.0 (현재)** — 이력서 기반 면접 질문 생성·평가, 키워드/토큰 기반 매칭(local v1), 위 "주요 기능" 전체.
- **v2.0 (계획)** — RAG 기반 매칭: pgvector + chunking + embedding + LangChain으로 공고 요구사항과 이력서를
  교차한 맞춤 질문·매칭, 이력서 OCR. 현재 미구현이며 계획 단계입니다.

## 참고

- 데모/포트폴리오용 프로젝트입니다. 데모 계정·비밀번호 관례는 운영 환경용이 아닙니다.
- `.env` 값, API 키, 토큰, 비밀은 커밋하지 않습니다.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`는 의도적으로 동기화하여 함께 갱신합니다.
