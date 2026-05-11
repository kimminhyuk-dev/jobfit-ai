AI 에이전트(Claude Code, Gemini CLI, ChatGPT 등)가 이 프로젝트에서 작업할 때 따라야 할 규칙과 컨텍스트 문서다.
**CLAUDE.md**와 **GEMINI.md**는 이 파일의 동일 복사본이다. 내용을 변경할 때는 세 파일을 동시에 갱신한다.

---

## 1. 프로젝트 개요

- **프로젝트명**: jobfit-ai
- **목적**: AI 기반 이력서-채용공고 매칭 플랫폼. 벡터 임베딩으로 매칭도를 계산하고 LLM이 강점·약점·개선 제안을 분석한다.
- **최신 상태 파악**: 작업 시작 전 반드시 루트의 `HANDOFF.md`를 먼저 읽는다.

---

## 2. 기술 스택

| 영역 | 기술 |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16 (Docker), Pydantic v2, python-jose, passlib[bcrypt] |
| Frontend | React 19, Next.js 16 App Router, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, TanStack Query, React Hook Form + Zod |
| AI/ML (예정) | Anthropic Claude API, sentence-transformers, pgvector, MCP Python SDK |
| Infra | Docker Compose, GitHub Actions (CI) |

---

## 3. 레이어드 아키텍처

```
api (router) → service → repository → model
```

- `api/`: 요청 수신·응답 반환만. 비즈니스 로직 금지.
- `services/`: 비즈니스 로직 전담. DB 직접 접근 금지.
- `repositories/`: DB 접근만. 비즈니스 로직 금지.
- `models/`: SQLAlchemy ORM. schema와 분리.
- `schemas/`: Pydantic DTO. ORM 모델과 분리.
- `core/`: `config.py`(설정), `database.py`(세션), `security.py`(JWT/bcrypt).

---

## 4. 인증 방식

- Access Token: JWT 15분, `Authorization: Bearer`
- Refresh Token: JWT 14일, HttpOnly Cookie, DB에 SHA-256 해시 저장 (취소·재사용 감지)
- 권한: `users.role` → USER / ADMIN
- 카테고리·Q&A 게시글 생성·수정·삭제는 ADMIN만 가능

---

## 5. 코딩 컨벤션

- Python: PEP 8, snake_case 함수/변수, PascalCase 클래스
- 동기 SQLAlchemy 세션을 쓰는 라우터는 `def`, 비동기 I/O 필요 시 `async def`
- DB 세션은 `deps.py`의 `get_db` 의존성 주입으로만 사용
- 환경 변수는 `core/config.py`의 `Settings` 클래스로만 접근
- `.env` 값·비밀키·토큰은 코드·문서에 절대 기록 금지

---

## 6. 개발 환경 명령어

```powershell
docker-compose up -d db
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m compileall app
```

---

## 7. AI 에이전트 작업 규칙

1. 작업 시작 전 `HANDOFF.md` 읽기
2. 작업 전 `git status --short` 확인
3. 사용자가 만든 변경사항을 되돌리지 않는다
4. 요청받은 기능과 직접 관련된 파일만 수정한다
5. 기존에 건드리지 않은 기능·결정사항은 유지한다
6. `.env` 값·비밀키·토큰 절대 출력/기록 금지
7. 작업 완료 후 `HANDOFF.md` 갱신
8. 새 파일 생성 전 동일 역할 파일 존재 여부 확인
9. 커밋 메시지: `feat/fix/refactor/docs/chore(scope): 설명`
10. AGENTS.md / CLAUDE.md / GEMINI.md 변경 시 세 파일 동시 갱신
