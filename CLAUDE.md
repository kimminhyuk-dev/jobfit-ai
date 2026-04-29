# AGENTS.md

AI 에이전트(Claude Code, Gemini CLI, ChatGPT 등)가 이 프로젝트에서 작업할 때 따라야 할 규칙과 컨텍스트 문서다.
**CLAUDE.md**와 **GEMINI.md**는 이 파일의 동일 복사본이다. 내용을 변경할 때는 세 파일을 동시에 갱신한다.

---

## 1. 프로젝트 개요

- **프로젝트명**: jobfit-ai
- **목적**: AI 기반 이력서-채용공고 매칭 플랫폼. 벡터 임베딩으로 매칭도를 계산하고 LLM이 강점·약점·개선 제안을 분석한다.
- **개발 단계**: 백엔드 인증 완료, 게시판/매칭 기능 개발 예정
- **최신 상태 파악**: 작업 시작 전 반드시 루트의 `HANDOFF.md`를 먼저 읽는다.

---

## 2. 기술 스택

### Backend
- Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic
- PostgreSQL 16 (Docker), Pydantic v2
- python-jose + passlib[bcrypt], httpx

### AI / ML (예정)
- Anthropic Claude API, sentence-transformers, pgvector / ChromaDB, MCP Python SDK

### Frontend (예정)
- React 19 + TypeScript, Vite, Tailwind CSS v4, shadcn/ui
- axios + TanStack Query, React Router v7, React Hook Form + Zod

### Infrastructure
- Docker + Docker Compose, GitHub Actions (CI)

---

## 3. 디렉터리 구조

```
jobfit-ai/
├── AGENTS.md          # AI 에이전트 지시 문서 (마스터)
├── CLAUDE.md          # AGENTS.md 복사본
├── GEMINI.md          # AGENTS.md 복사본
├── HANDOFF.md         # AI 인수인계 기준 문서
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/       # HTTP 라우터 계층
│   │   │   ├── auth.py
│   │   │   └── deps.py
│   │   ├── core/      # 설정·DB·보안 공통 모듈
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/    # SQLAlchemy ORM 모델
│   │   ├── repositories/  # DB 접근 계층
│   │   ├── schemas/   # 요청/응답 DTO (Pydantic)
│   │   ├── services/  # 비즈니스 로직 계층
│   │   └── main.py
│   ├── alembic/
│   ├── .env.example
│   └── requirements.txt
├── frontend/          # React 앱 (미착수)
└── ai_context/        # 상세 작업 문서
    ├── API_SPEC.md
    ├── ARCHITECTURE.md
    ├── PROJECT_STATE.md
    ├── TASKS.md
    └── WORK_LOG.md
```

---

## 4. 레이어드 아키텍처 규칙

```
api (router) → service → repository → model
```

- `api/`: 요청 수신, 응답 반환만. 비즈니스 로직 금지.
- `services/`: 비즈니스 로직 전담. DB 직접 접근 금지.
- `repositories/`: DB 접근만. 비즈니스 로직 금지.
- `models/`: SQLAlchemy ORM 정의. schema와 분리 유지.
- `schemas/`: Pydantic DTO. ORM 모델과 분리 유지.
- `core/`: 설정(`config.py`), DB 세션(`database.py`), JWT·bcrypt(`security.py`).

---

## 5. 코딩 컨벤션

- Python 파일은 PEP 8 준수.
- 함수·변수명은 snake_case, 클래스명은 PascalCase.
- 비동기 I/O가 필요한 엔드포인트는 `async def`를 사용하고, 현재처럼 동기 SQLAlchemy 세션을 쓰는 라우터는 `def`를 유지한다.
- DB 세션은 `deps.py`의 `get_db` 의존성 주입으로만 사용.
- 환경 변수는 `core/config.py`의 `Settings` 클래스를 통해서만 접근.
- `.env` 값, 비밀키, 토큰은 코드나 문서에 절대 기록하지 않는다.

---

## 6. 인증 방식

- Access Token: JWT, 만료 15분, `Authorization: Bearer` 헤더
- Refresh Token: JWT, 기본 만료 14일, HttpOnly Cookie (`refresh_token`)
- Refresh Rotation: 재발급 시 새 Refresh Token 발급

---

## 7. 개발 환경 명령어

```powershell
# Docker PostgreSQL 실행
docker-compose up -d db

# 백엔드 가상환경 진입
cd backend
.\.venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt

# Alembic 마이그레이션 적용
alembic upgrade head

# 개발 서버 실행 (포그라운드)
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 문법 검사
python -m compileall app
```

---

## 8. AI 에이전트 작업 규칙

1. **작업 시작 전** `HANDOFF.md`를 읽어 현재 상태를 파악한다.
2. **작업 전** `git status --short`로 변경사항을 확인한다.
3. **사용자가 만든 변경사항을 되돌리지 않는다.**
4. **요청받은 기능과 직접 관련된 파일만 수정한다.**
5. **기존에 건드리지 않은 기능·결정사항은 유지한다.**
6. **`.env` 값, 비밀키, 토큰은 절대 출력하거나 문서에 기록하지 않는다.**
7. **작업 완료 후** `HANDOFF.md`의 해당 섹션(현재 상태, 완료 기능, 최근 검증, 다음 작업)을 갱신한다.
8. **새 파일을 만들기 전** 동일한 역할의 파일이 이미 있는지 확인한다.
9. 커밋 메시지는 `feat/fix/refactor/docs/chore(scope): 설명` 형식을 따른다.
10. AGENTS.md / CLAUDE.md / GEMINI.md 내용을 변경할 경우 세 파일을 동시에 갱신한다.
