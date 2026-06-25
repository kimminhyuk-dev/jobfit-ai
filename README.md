# JobFit AI 🎯

AI 기반 이력서·채용공고 매칭 플랫폼입니다. 이력서를 업로드하면 AI가 내용을 파싱·구조화하고, 채용공고와의 적합도를 산출하며, **공고 요구사항과 이력서 경험을 교차한 맞춤형 면접 질문**까지 생성합니다. `USER` · `COMPANY` · `ADMIN` 세 역할로 구성되어, 이력서 관리부터 공고 탐색·지원·면접 연습까지 end-to-end 흐름을 다룹니다.

> **v1 → v2 진화**: v1은 **키워드/토큰 기반** 매칭과 이력서 단독 면접 질문 생성 단계였고, **v2에서 RAG(검색 증강 생성)를 도입**해 pgvector 의미 검색 + LangChain 기반 공고 맞춤 질문으로 발전시켰습니다.

![Status](https://img.shields.io/badge/Status-v2.0%20RAG%20도입%20완료-2EA44F?style=flat)
![Type](https://img.shields.io/badge/Type-개인%20포트폴리오-4B5563?style=flat)
![License](https://img.shields.io/badge/License-MIT-3DA639?style=flat)

**Backend**
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=flat&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-1.18-6BA81E?style=flat)
![Pydantic](https://img.shields.io/badge/Pydantic-2-E92063?style=flat&logo=pydantic&logoColor=white)

**AI / RAG**
![LangChain](https://img.shields.io/badge/LangChain-1.3-1C3C3C?style=flat&logo=langchain&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-0.4-4169E1?style=flat&logo=postgresql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings%20%26%20Chat-412991?style=flat&logo=openai&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Gemini-Resume%20Parsing-8E75B2?style=flat&logo=googlegemini&logoColor=white)

**Frontend**
![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?style=flat&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-4-06B6D4?style=flat&logo=tailwindcss&logoColor=white)
![TanStack Query](https://img.shields.io/badge/TanStack%20Query-5-FF4154?style=flat&logo=reactquery&logoColor=white)
![Zod](https://img.shields.io/badge/Zod-4-3E67B1?style=flat&logo=zod&logoColor=white)

**Database / Infra / Auth**
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Access%20%2F%20Refresh-000000?style=flat&logo=jsonwebtokens&logoColor=white)

---

## 📌 프로젝트 배경

채용 시장에서 구직자는 "내 이력서가 이 공고에 얼마나 맞는지", "이 공고 면접에서 뭘 물어볼지"를 스스로 가늠하기 어렵습니다. JobFit AI는 이 두 질문에 답하는 것을 목표로 시작했습니다.

이력서 파싱(LLM 구조화)부터 공고 탐색·지원, 적합도 점수 산출, 면접 질문 생성까지 실제 채용 서비스에 가까운 흐름을 직접 구현하면서, **단순 LLM 호출을 넘어 RAG·임베딩·벡터 검색을 실제 제품 흐름에 녹이는 것**에 중점을 두었습니다. 초기 v1은 키워드 기반 매칭으로 흐름을 완성했고, v2에서 RAG를 도입해 "이력서의 어떤 경험이 이 공고와 의미적으로 연결되는가"를 벡터 유사도로 찾도록 고도화했습니다.

---

## ✨ 주요 기능

### 🔐 인증 / 계정
- 회원가입 · 로그인 · 토큰 리프레시 · 로그아웃 · 현재 사용자 조회 · 프로필 수정 · 회원 탈퇴
- **로그인 포털 분리** — `/login`은 USER 전용, `/company/login`은 COMPANY·ADMIN(이메일 또는 사업자번호 10자리)
- **계정 복구** — 이메일(아이디) 찾기, 비밀번호 재설정 (개인·기업 각각)

### 📄 이력서
- 업로드 및 파싱 — PDF/DOCX 텍스트 추출 + **Google Gemini** 구조화
- 구조화된 프로젝트 · 자기소개서 섹션 관리
- **업로드 시 자동 청킹** — 업로드 성공 후 백그라운드로 이력서를 청킹·임베딩해 벡터 저장(응답을 막지 않음)

### 🧠 면접 연습 / 질문 생성 (AI)
- **v1 — 이력서 기반 면접 연습 (OpenAI)**: 세션 생성 시 5문항을 1회 생성·저장하고, 답변을 한 건씩 평가. 세션 조회는 LLM을 호출하지 않음
- **v2 — 공고 맞춤 면접질문 (RAG + LangChain)**: 지원한 공고의 요구사항과 이력서 chunk를 의미 검색으로 엮어, 워밍업→직무 기초→경험 기반→심화 순서의 질문 5개를 생성

### 🏢 채용공고 / 지원
- 공고 목록 · 상세 · 필터(출처 · 키워드 · 지역 · 학력 · 고용형태 · NCS 분류) · 페이지네이션
- 선택한 이력서로 공고 지원, 동일 `(user_id, job_id)` 활성 **중복 지원 차단**, 지원 내역 조회·취소
- **매칭 점수** — 지원 시 이력서·공고를 비교해 점수와 근거를 산출·저장 (`local-match-v1`, 알고리즘 버전 `1.0.0`)
- **면접 메일** — 회사가 지원자에게 면접 안내 메일을 발송(SMTP)하고 Google Maps Static 지도 이미지를 첨부

### 👥 회사 / 게시판 / 관리자
- **회사** — 받은 지원 대시보드, 지원자 이력서 조회·상태 변경, 공고 등록·수정·삭제 (지원 공고는 자동 프로비저닝)
- **게시판** — 카테고리 · Q&A 게시글 (생성/수정/삭제는 ADMIN 전용)
- **RBAC** — 역할(roles) · 권한(permissions) · 사용자-역할(user_roles)과 `require_permission` 기반 권한 판정
- **휴가 결재** — RBAC 기반 신청 · 결재선 · 직무 분리 · 잔여 관리
- **관리자** — 통계, 사용자 관리, 역할 부여·회수, 감사 로그, 공통코드, 동적 메뉴, 채용공고 관리

---

## 🧠 RAG 파이프라인 (v2 핵심)

이력서를 벡터로 색인하고, 공고 요구사항으로 의미 검색해, 그 컨텍스트로 면접 질문을 생성하는 end-to-end RAG 흐름입니다.

```text
이력서 업로드 ─▶ 청킹 ─▶ 임베딩 ─▶ pgvector 저장
                                         │
공고 요구사항 ─▶ 쿼리 임베딩 ─▶ 코사인 의미 검색(top-k) ─┘
                                         │
                             LangChain(PromptTemplate | ChatOpenAI | PydanticOutputParser)
                                         │
                                  공고 맞춤 면접 질문 5개
```

| 단계 | 구현 | 비고 |
|---|---|---|
| **청킹** | `rag/chunking.py` — `parsed_data` · 프로젝트 · 자소서 섹션을 섹션별 텍스트로 모으고, 500자 초과 섹션은 문단·문장 경계 우선 분할 | 인접 chunk 약 50자(≈10%) overlap |
| **임베딩** | `rag/embedding.py` — OpenAI `text-embedding-3-small`로 배치 임베딩, 1536차원 검증 | `dimensions` 파라미터 미전송 |
| **저장** | `ResumeChunk` 모델 → `resume_chunks` 테이블, `embedding Vector(1536)`, `resume_id` `ON DELETE CASCADE` | HNSW 인덱스(`vector_cosine_ops`) |
| **검색** | `rag/retrieval.py` — `build_job_query_text(job)`로 공고 요구 쿼리 구성 → 코사인 거리순 chunk 검색 | 단일 이력서 스코프 |
| **생성** | `job_based_interview_service.py` — top-k=7 chunk를 LangChain 체인에 주입, 1회 LLM 호출로 질문 5개 | `PydanticOutputParser` 구조화 출력 |

**주요 엔드포인트**

| Method · Path | 설명 |
|---|---|
| `POST /resumes/{id}/chunks/rebuild` | 이력서 수동 재청킹·임베딩 (멱등, 내용 동일 시 임베딩 스킵) |
| `POST /resumes/{id}/retrieve` | 공고 요구(또는 직접 쿼리) 기반 이력서 chunk 의미 검색 |
| `POST /resumes/{id}/interview-questions/job-based` | 공고 맞춤 면접질문 생성 (`{ job_id }`) |
| `POST /resumes` (업로드) | 성공 후 `BackgroundTasks`로 자동 청킹 예약 |

> 자동 청킹은 `skip_if_unchanged=True`로 동작해, `(section, chunk_index, content)`가 기존과 동일하면 OpenAI 임베딩 호출 없이 스킵합니다(비용 절감).

---

## 🛠️ 기술 스택 (확인된 버전)

### Backend — `backend/requirements.txt`

| 영역 | 스택 |
|---|---|
| 언어/프레임워크 | Python, FastAPI 0.136.0, Starlette 1.0.0 |
| ORM/마이그레이션 | SQLAlchemy 2.0.49, Alembic 1.18.4 |
| 검증/설정 | Pydantic 2.13.3, pydantic-settings 2.14.0 |
| 서버 | Uvicorn 0.46.0 |
| DB 드라이버 / 벡터 | psycopg 3.3.3, **pgvector 0.4.2** |
| **RAG / LLM 오케스트레이션** | **LangChain 1.3.11, langchain-openai 1.3.3** (langgraph 1.2.6) |
| 인증 | python-jose 3.5.0, passlib 1.7.4, bcrypt 4.0.1 |
| 이력서 파일 처리 | pdfplumber 0.11.9, pypdf 6.10.2, python-docx 1.2.0 |
| AI SDK | openai 2.41.0, google-generativeai 0.8.5 |

### Frontend — `frontend/package.json`

| 영역 | 스택 |
|---|---|
| 프레임워크 | Next.js 16 (App Router), React 19 |
| 언어 | TypeScript 6 |
| 스타일 | Tailwind CSS 4 |
| 상태/폼 | TanStack Query 5, React Hook Form 7, Zod 4 |
| HTTP/아이콘 | axios 1, lucide-react 1 |

### Database / Infra
- **PostgreSQL 16 + pgvector** (`pgvector/pgvector:pg16`), Docker Compose

### LLM (용도별 모델 분리)

| 용도 | 모델 | 비고 |
|---|---|---|
| 면접 질문 생성·평가 (v1) | OpenAI (`settings.openai_model`, 기본 `gpt-5-mini`) | reasoning effort `low` |
| 공고 맞춤 면접질문 (v2) | OpenAI via LangChain `ChatOpenAI` | `PromptTemplate \| ChatOpenAI \| PydanticOutputParser` |
| 이력서 임베딩 (v2) | OpenAI `text-embedding-3-small` | 1536차원 |
| 이력서 파싱·구조화 | Google Gemini | `gemini-2.5-flash-lite` → `gemini-2.0-flash-lite` → `gemini-2.5-flash` 폴백 체인 |

---

## 📂 프로젝트 구조

```text
jobfit-ai/
├── backend/                      # FastAPI + SQLAlchemy (포트 8000)
│   ├── alembic/                  # 마이그레이션 (pgvector 확장, resume_chunks ...)
│   └── app/
│       ├── api/                  # FastAPI 라우터 (요청/응답만)
│       ├── services/             # 비즈니스 로직
│       │   └── rag/              # 🧠 chunking · embedding · retrieval · resume_chunk_service
│       ├── repositories/         # DB 접근 전용
│       ├── models/               # SQLAlchemy ORM (ResumeChunk, User, JobPosting ...)
│       ├── schemas/              # Pydantic DTO
│       ├── core/                 # config, database/session, security, errors
│       ├── prompts/              # 서버 측 AI 프롬프트·레퍼런스
│       └── scripts/              # 데모 시드 / 목 데이터 생성
├── frontend/                     # Next.js 16 App Router (포트 3000)
│   └── src/
│       ├── app/                  # 라우트 (user, company, admin, login ...)
│       ├── screens/              # 페이지 단위 UI
│       ├── components/           # 공용 컴포넌트
│       ├── api/                  # API 클라이언트·타입
│       └── stores/               # 클라이언트 상태
└── docker-compose.yml            # PostgreSQL(pgvector) 16
```

아키텍처: **React (Next.js, axios) → FastAPI 라우터 → Service → Repository → Model(SQLAlchemy) → PostgreSQL(pgvector)**

```text
api (router) -> service -> repository -> model
```
- `api/`: 요청 수신·응답 반환만 — 비즈니스 로직 없음
- `services/`: 비즈니스 로직. 리포지토리 메서드가 있으면 직접 DB 쿼리하지 않음
- `repositories/`: DB 접근 전용
- `models/`(ORM)와 `schemas/`(DTO)는 분리

---

## 🚀 실행 방법

### 사전 요구사항
- Python 3.12, Node.js, Docker Desktop (PostgreSQL 실행용)
- `.env`에 `OPENAI_API_KEY`(면접질문·임베딩), `GEMINI_API_KEY`(이력서 파싱) 등 필요 키 설정 — 실제 키/비밀은 절대 커밋하지 않음

### Backend

```powershell
docker-compose up -d postgres          # PostgreSQL + pgvector (5432)
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head                    # pgvector 확장 + resume_chunks 포함
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev                             # http://localhost:3000
```

### 루트 헬퍼 (레포 루트에서 두 앱 동시 실행)

```powershell
npm run dev     # backend + frontend 동시 실행 (concurrently)
npm run lint    # frontend lint
npm run build   # frontend build
```

### 검증

```powershell
cd backend;  .\.venv\Scripts\python.exe -m compileall app
cd ..\frontend;  npm run lint;  npm run build
```

---

## 🔒 보안 구현

코드에서 실제로 적용된 항목입니다.

- **비밀번호 해싱** — passlib + bcrypt로 저장, 응답에서 비밀번호 제외
- **JWT Access/Refresh 토큰** — Access 15분(쿠키 기반), Refresh 14일(HttpOnly 쿠키), **DB에 SHA-256 해시 저장**해 무효화 가능
- **401 자동 갱신** — 클라이언트 axios 인터셉터가 401 시 refresh로 토큰 자동 재발급 후 원 요청 재시도
- **RBAC** — `require_permission` 의존성 + `roles`/`permissions`/`user_roles`로 기능 권한 판정 (관리자 API 보호)
- **소유권 검증** — 이력서 청킹/검색/면접질문은 본인 또는 ADMIN만 허용, 타인 리소스는 404로 차단
- **민감정보 비노출** — 422 검증 오류 응답에서 raw `input` 값 제거(비밀번호/토큰류 echo 방지), 시크릿/키 로깅 금지
- **공고 직접 접근 차단** — `status='HIDDEN'` 공고는 상세 직접 조회 시에도 404
- **시크릿 분리** — 모든 키/비밀은 `.env`(gitignore)로 관리, 저장소 이력에 미포함

---

## 🗺️ 버전 & 로드맵

### ✅ v1.0 — RAG 도입 전
- 회원/인증, 소셜 포털 분리, JWT + 인터셉터 자동 갱신, RBAC, 휴가 결재
- 이력서 업로드·파싱(Gemini), 공고 조회·필터·지원, 관리자 기능
- **키워드/토큰 기반** 매칭(`local-match-v1`), 이력서 단독 OpenAI 면접 질문 생성·평가

### ✅ v2.0 — RAG 도입 후 (현재)
- **pgvector 도입** — `pgvector/pgvector:pg16` 이미지 교체 + `vector` 확장
- **이력서 청킹 → 임베딩(`text-embedding-3-small`, 1536) → `resume_chunks`(HNSW) 저장**
- **공고 요구 기반 이력서 chunk 의미 검색**(코사인 거리)
- **LangChain 공고 맞춤 면접질문 생성** + 업로드 시 자동 청킹(백그라운드, 멱등)

### 🔜 계획 (회고 기반)
- 임베딩 기반 **지원 적합도 매칭**으로 `local-match-v1` 대체/보강 (현재 매칭은 결정적 로컬 방식)
- 항공편/공고 OpenAPI 주기적 배치 수집 + 관리자 데이터 확인 화면
- 관리자 등급(A/B/C) 세분화 및 권한별 기능 분리
- 삭제 등 주요 작업의 관리 로그(관리자 ID·IP·시각) 추적

---

## 🧩 트러블슈팅 — RAG 재청킹 원자성 (임베딩 실패 시 기존 데이터 보존)

**문제** 초기 `rebuild_resume_chunks`는 같은 이력서의 기존 chunk를 **먼저 삭제한 뒤** OpenAI 임베딩을 호출했습니다. 삭제·삽입이 한 트랜잭션이라도, 네트워크 임베딩 호출이 트랜잭션을 길게 점유했고, **임베딩이 실패하면 기존 chunk가 이미 사라져 "실패 시 기존 데이터 보존" 요구를 만족하지 못했습니다.**

**해결** (`fix(rag): rebuild를 임베딩 후 원자적 교체로 변경`) 순서를 뒤집어, **청킹과 임베딩을 먼저 모두 끝낸 뒤** "기존 chunk 삭제 + 새 chunk 삽입"만 하나의 짧은 트랜잭션으로 묶어 **원자적으로 교체**하도록 했습니다. 임베딩 단계에서 실패하면 DB는 손대지 않으므로 기존 데이터가 그대로 보존됩니다. 멱등성도 함께 확보해, 같은 이력서를 다시 청킹해도 chunk가 중복으로 쌓이지 않습니다.

> 참고 — 단일 이력서 스코프 검색은 `WHERE resume_id=:r` + 코사인 `ORDER BY ... LIMIT` 계획상 소량 행에 대한 Seq Scan + Sort로 잡힙니다. 이는 버그가 아니라 의도된 계획이며, 전 이력서 글로벌 ANN이 필요해지면 HNSW 인덱스(`ix_resume_chunks_embedding_hnsw`)를 활용하는 별도 전략을 고려합니다.

---

## ⚠️ 면책 조항

- 본 저장소는 **개인 포트폴리오 및 학습 목적**으로 공개됩니다.
- OpenAI · Google Gemini 등 외부 API 키는 포함되어 있지 않으며(`.env`로 분리), 데모 계정·비밀번호 관례는 운영 환경용이 아닙니다.
- 실제 채용·개인정보 처리를 위한 상용 서비스가 아니며, 시연 데이터는 더미 데이터입니다.
- `AGENTS.md` · `CLAUDE.md` · `GEMINI.md`는 의도적으로 동기화하여 함께 갱신합니다.

---

## 🔗 Link

GitHub: https://github.com/kimminhyuk-dev/jobfit-ai
