# API_SPEC

## 공통

**에러 응답** `{ "code": "AUTH_001", "message": "..." }` — 검증 오류는 `details[]` 포함

**주요 에러코드**
- `COMMON_001` 검증 실패, `COMMON_404` 리소스 없음
- `AUTH_001~007` 인증/권한/이메일중복/비밀번호불일치/비활성/리프레시없음/유효하지않음
- `CATEGORY_001~002`, `POST_001~002`, `JOB_001~005`, `JOB_SOURCE_001`, `BATCH_001~002`, `CODE_001`

---

## 인증 `/auth`

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | /auth/signup | 회원가입 → Access Token 응답 + Refresh Token Cookie |
| POST | /auth/login | 로그인 → 동일 |
| POST | /auth/refresh | Refresh Token 검증 → 새 토큰 발급 |
| POST | /auth/logout | Refresh Token Cookie 삭제 |
| GET | /auth/me | 현재 사용자 조회 |
| PATCH | /auth/me | 이름·비밀번호 수정 |

**공통 응답** (signup/login/refresh)
```json
{ "access_token": "...", "token_type": "bearer", "expires_in": 900, "user": { "user_id": 1, "email": "...", "name": "...", "status": "ACTIVE" } }
```

---

## 게시판

**카테고리** (ADMIN 쓰기, USER 읽기)
- `GET /categories` — 목록, `POST /categories` — 생성
- `GET/PATCH/DELETE /categories/{id}`

**게시글**
- `GET /posts?offset&limit&category_id` — 목록
- `POST /posts` — ADMIN 생성
- `GET/PATCH/DELETE /posts/{id}`

---

## 채용공고

### GET /jobs
```
?source=ALIO&keyword=&data_source=PRODUCTION&page=1&size=20
```
`data_source`: PRODUCTION / MOCK / MANUAL

### POST /admin/job-sources/alio/collect (ADMIN)
ALIO 수집 수동 실행. `{ keyword, start_page, max_pages, display, idempotency_key }`
→ `{ job_code, status, collected_count, inserted_count, ... }`

### POST /admin/jobs/sources/work24/collect (ADMIN)
Work24 — PENDING_APPROVAL 상태로 외부 호출 없이 BLOCKED 이력만 기록 (`JOB_SOURCE_001`)

### POST /admin/jobs/sources/mock/load (ADMIN)
`backend/data/mock_work24_jobs.json` → `data_source="MOCK"` 저장

---

## 이력서

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | /resumes | 업로드 (PDF/DOCX/TXT ≤10MB), 파싱 저장 |
| GET | /resumes | 내 목록 |
| GET | /resumes/{id} | 상세 + 파싱 결과 |
| GET | /resumes/{id}/file | 원본 파일 스트리밍 |
| DELETE | /resumes/{id} | 소프트 삭제 + 파일 삭제 |

---

## 관리자 이력서/사용자

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | /admin/users | 사용자 목록 |
| GET | /admin/users/{id} | 사용자 상세 + 이력서 목록 |
| GET | /admin/users/resumes/{id} | 이력서 상세 + `structured_projects` + `structured_cover_letter_sections` |
| PATCH | /admin/users/resumes/{id} | 이력서 제목/원문/파싱/구조화 데이터 수정 |
| GET | /admin/users/resumes/{id}/file | 원본 파일 스트리밍 |
| GET | /admin/stats | 통계 요약 |

**PATCH 구조화 필드**: `structured_projects` 전송 시 `resume_projects` 전체 교체(delete-insert), `structured_cover_letter_sections` 전송 시 `resume_cover_letter_sections` 전체 교체. 생략 시 `parsed_data`에서 자동 동기화.

---

## DB 설계 메모

- `job_postings.source + source_job_id` 유니크 (중복 수집 방지)
- `job_sources` 상태: ALIO=ACTIVE, WORK24=PENDING_APPROVAL, SARAMIN=DISABLED, MANUAL=ACTIVE
- `resume_projects` 컬럼: name, period, role, description, review, tech_stack(JSON), raw_text
- `resume_cover_letter_sections` 컬럼: title, content
- 두 테이블 모두 CASCADE 삭제, AuditMixin 적용
