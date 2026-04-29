# JobFit AI

> AI 기반 이력서-채용공고 매칭 플랫폼. 이력서와 공고를 벡터 임베딩으로 분석하고, LLM이 매칭도·강점·약점을 해석해 커리어 의사결정을 돕습니다. MCP(Model Context Protocol) 서버를 통해 Claude Desktop에서 자연어로 직접 조회·상담할 수 있습니다.

**Status**: 🚧 개발 중 (2026.04 ~ )

---

## 프로젝트 배경

취업 준비 과정에서 겪은 문제 의식에서 출발한 개인 포트폴리오 프로젝트입니다.

- 채용공고는 쏟아지지만 "내 이력서와 얼마나 맞는지" 객관적으로 확인하기 어렵다
- LLM(ChatGPT, Claude)에 물어보면 답은 잘 해주지만, 매번 이력서와 공고를 수동으로 붙여넣어야 한다
- MCP(Model Context Protocol)를 활용하면 AI 비서에게 영구적인 커리어 컨텍스트를 제공할 수 있지 않을까?

## 주요 기능 (계획)

### 핵심 기능
- 📄 이력서 업로드 (PDF/DOCX 파싱 → 구조화)
- 🔍 채용공고 자동 수집 (사람인 API / 공공데이터 API / 수동 입력)
- 🎯 이력서-공고 매칭도 계산 (벡터 임베딩 기반 코사인 유사도)
- 🤖 LLM 분석 (강점·약점·개선 제안)
- ⭐ 즐겨찾기 및 지원 이력 관리

## 기술 스택

### Backend
- **FastAPI** (Python 3.12+)
- **SQLAlchemy 2.0** + Alembic
- **PostgreSQL 16**
- **Pydantic v2**
- **python-jose** + passlib[bcrypt]
- **httpx** (외부 API 비동기 호출)

### AI / ML
- **Anthropic Claude API** (LLM 호출)
- **sentence-transformers** (한국어 임베딩)
- **pgvector** 또는 ChromaDB (벡터 저장소)
- **MCP Python SDK**

### Frontend
- **React 19** + TypeScript
- **Vite 8**
- **Tailwind CSS v4**
- **axios**
- **TanStack Query**
- **React Router v7**
- **React Hook Form** + Zod
- **shadcn/ui 스타일 컴포넌트** (Radix Slot, CVA, tailwind-merge 기반)

### Infrastructure
- **Docker** + Docker Compose
- **GitHub Actions** (CI)

> 수집된 공고 데이터는 상업적 재배포 없이 개인 포트폴리오 시연 및 기능 학습 목적으로만 사용합니다.

## 로드맵

- [x] 프로젝트 기획 및 기술 스택 결정
- [x] 개발환경 세팅 (Docker, FastAPI 뼈대)
- [x] 회원/인증 시스템 (JWT + Refresh Rotation)
- [ ] 권한/메뉴 관리 (RBAC + 매트릭스)
- [x] 관리자 권한 기반 카테고리/Q&A 게시판 CRUD API
- [x] 공통 에러코드 기반 API 에러 응답
- [ ] 이력서 파싱 (PDF → 구조화 데이터)
- [ ] 공고 수집 파이프라인
- [ ] 벡터 임베딩 + 매칭 알고리즘
- [ ] LLM 분석 레이어
- [x] React 19 + Tailwind CSS 프론트엔드 초기 구현
- [x] TanStack Query / React Hook Form / Zod / shadcn 스타일 UI 기반 반영
- [x] Vite 8 / Tailwind CSS v4 전환 및 프론트엔드 도구체인 최신화
- [ ] 프론트엔드 관리자 카테고리/Q&A 화면 실제 API 연결
- [ ] MCP 서버 구현
- [ ] Docker Compose 통합 배포
- [ ] 데모 영상 및 문서화

## 면책 조항

- 본 프로젝트는 개인 포트폴리오 및 기술 학습 목적으로 제작됩니다
- 채용 결정 또는 고용 조언의 공식 도구가 아닙니다
- 외부 API에서 수집된 데이터의 재배포 없이 개인 사용에 한정합니다
