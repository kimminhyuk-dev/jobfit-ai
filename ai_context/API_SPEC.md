# API_SPEC

## 공통 에러 응답

API 에러 응답은 공통 에러코드 기반으로 내려준다.

```json
{
  "code": "AUTH_001",
  "message": "인증 정보가 유효하지 않습니다."
}
```

입력값 검증 오류는 `details` 배열을 추가로 포함한다.

```json
{
  "code": "COMMON_001",
  "message": "요청 값이 올바르지 않습니다.",
  "details": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

### 주요 에러코드

- `COMMON_001` — 요청 값 검증 실패
- `COMMON_404` — 요청한 리소스 없음
- `COMMON_405` — 허용되지 않은 요청 방식
- `AUTH_001` — 인증 정보가 없거나 유효하지 않음
- `AUTH_002` — 접근 권한 없음
- `AUTH_003` — 이미 가입된 이메일
- `AUTH_004` — 로그인 정보 불일치
- `AUTH_005` — 비활성 계정
- `AUTH_006` — Refresh Token 없음
- `AUTH_007` — Refresh Token 유효하지 않음
- `CATEGORY_001` — 카테고리 없음
- `CATEGORY_002` — 카테고리 slug 중복
- `POST_001` — 게시글 없음
- `POST_002` — 활성 카테고리 없음
- `JOB_001` — 채용공고 없음
- `JOB_002` — 채용공고 수집 실패
- `JOB_003` — 외부 API 호출 실패
- `JOB_004` — 외부 채용 API 응답 파싱 실패
- `JOB_005` — 외부 API 키 미설정
- `JOB_SOURCE_001` — 현재 사용할 수 없는 채용공고 수집원
- `BATCH_001` — 배치 실행 실패
- `BATCH_002` — 배치 실행 이력 없음
- `CODE_001` — 공통코드 없음

## 인증

### POST /auth/signup
회원가입 후 Access Token을 응답하고 Refresh Token은 HttpOnly 쿠키로 내려준다.

#### Request
```json
{
  "email": "string",
  "password": "string",
  "name": "string"
}
```

#### Response 201
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "user_id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "status": "ACTIVE",
    "created_at": "2026-04-29T00:00:00Z",
    "updated_at": "2026-04-29T00:00:00Z"
  }
}
```

### POST /auth/login
로그인 후 Access Token을 응답하고 Refresh Token은 HttpOnly 쿠키로 내려준다.

#### Request
```json
{
  "email": "string",
  "password": "string"
}
```

#### Response 200
`POST /auth/signup` 응답과 동일하다.

### POST /auth/refresh
Refresh Token 쿠키를 검증하고 새 Access Token과 Refresh Token을 발급한다.

#### Response 200
`POST /auth/signup` 응답과 동일하다.

### POST /auth/logout
Refresh Token 쿠키를 삭제한다.

#### Response 200
```json
{
  "message": "로그아웃되었습니다."
}
```

### GET /auth/me
Bearer Access Token으로 현재 로그인 사용자를 조회한다.

#### Header
```http
Authorization: Bearer <access_token>
```

#### Response 200
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "name": "홍길동",
  "status": "ACTIVE",
  "created_at": "2026-04-29T00:00:00Z",
  "updated_at": "2026-04-29T00:00:00Z"
}
```

## 게시글

## 카테고리

### GET /categories
활성 카테고리 목록을 조회한다.

#### Response 200
```json
[
  {
    "category_id": 1,
    "name": "FAQ",
    "slug": "faq",
    "description": "자주 묻는 질문",
    "sort_order": 1,
    "is_active": true,
    "created_at": "2026-04-29T00:00:00Z",
    "updated_at": "2026-04-29T00:00:00Z"
  }
]
```

### POST /categories
관리자가 카테고리를 생성한다.

#### Header
```http
Authorization: Bearer <admin_access_token>
```

#### Request
```json
{
  "name": "FAQ",
  "slug": "faq",
  "description": "자주 묻는 질문",
  "sort_order": 1,
  "is_active": true
}
```

#### Response 201
`GET /categories`의 단일 객체와 동일하다.

### GET /categories/{category_id}
활성 카테고리 상세를 조회한다.

#### Response 200
`GET /categories`의 단일 객체와 동일하다.

### PATCH /categories/{category_id}
관리자가 카테고리를 수정한다.

#### Header
```http
Authorization: Bearer <admin_access_token>
```

#### Request
```json
{
  "name": "FAQ",
  "slug": "faq",
  "description": "자주 묻는 질문",
  "sort_order": 1,
  "is_active": true
}
```

#### Response 200
`GET /categories`의 단일 객체와 동일하다.

### DELETE /categories/{category_id}
관리자가 카테고리를 소프트 삭제한다.

#### Header
```http
Authorization: Bearer <admin_access_token>
```

#### Response 204
응답 본문 없음.

### GET /posts
Q&A 게시글 목록을 조회한다.

#### Query
```http
offset=0
limit=20
category_id=1
```

#### Response 200
```json
[
  {
    "post_id": 1,
    "author_id": 1,
    "category_id": 1,
    "title": "첫 게시글",
    "content": "본문입니다.",
    "created_at": "2026-04-29T00:00:00Z",
    "updated_at": "2026-04-29T00:00:00Z"
  }
]
```

### POST /posts
관리자가 Q&A 게시글을 생성한다.

#### Header
```http
Authorization: Bearer <admin_access_token>
```

#### Request
```json
{
  "category_id": 1,
  "title": "string",
  "content": "string"
}
```

#### Response 201
```json
{
  "post_id": 1,
  "author_id": 1,
  "category_id": 1,
  "title": "첫 게시글",
  "content": "본문입니다.",
  "created_at": "2026-04-29T00:00:00Z",
  "updated_at": "2026-04-29T00:00:00Z"
}
```

### GET /posts/{post_id}
게시글 상세를 조회한다.

#### Response 200
`POST /posts` 응답과 동일하다.

### PATCH /posts/{post_id}
관리자가 Q&A 게시글을 수정한다.

#### Header
```http
Authorization: Bearer <admin_access_token>
```

#### Request
```json
{
  "category_id": 1,
  "title": "string",
  "content": "string"
}
```

#### Response 200
`POST /posts` 응답과 동일하다.

### DELETE /posts/{post_id}
관리자가 Q&A 게시글을 소프트 삭제한다.

#### Header
```http
Authorization: Bearer <admin_access_token>
```

#### Response 204
응답 본문 없음.

## 채용공고 수집 (관리자)

### POST /admin/job-sources/alio/collect
관리자가 ALIO 공공기관 채용정보 목록 API 수집을 수동 실행한다.

ALIO가 현재 메인 공공기관 채용 수집원이다. API 키는 `backend/.env`에서
`ALIO_API_KEY`로 관리하며, 실제 키 값은 요청/응답/문서에 포함하지 않는다.
자동 배치는 추후 GitHub Actions, Jenkins, APScheduler 등으로 확장하고,
현재는 관리자 수동 수집 API로 먼저 검증한다.

#### Header
```http
Authorization: Bearer <admin_access_token>
```

#### Request
```json
{
  "keyword": "python",
  "start_page": 1,
  "max_pages": 3,
  "display": 10
}
```

#### Response 200
```json
{
  "job_code": "ALIO_RECRUIT_COLLECT",
  "status": "SUCCESS",
  "collected_count": 30,
  "inserted_count": 20,
  "updated_count": 10,
  "failed_count": 0,
  "run_id": 1
}
```

### POST /admin/jobs/sources/work24/collect
관리자가 Work24/고용24 채용정보 목록 API 수집을 수동 실행한다.

Work24/고용24는 키는 발급됐으나 일반 사용자 API 사용 제한으로 보류 상태다.
수집원 상태는 `job_sources` 테이블에서 관리하며, WORK24는 `PENDING_APPROVAL`
상태로 seed된다. 기존 코드는 삭제하지 않고 유지하되, `ACTIVE`가 아닌 수집원은
환경변수 값과 무관하게 외부 API를 호출하지 않고 `batch_job_runs`에
`JOB_SOURCE_001` 차단 이력을 남긴다. 이전 테스트에서 사용한 `idempotency_key`가
있어도 기존 성공 run을 재사용하지 않는다.

#### Header
```http
Authorization: Bearer <admin_access_token>
```

#### Request
```json
{
  "keyword": "python",
  "start_page": 1,
  "max_pages": 1,
  "display": 10,
  "region": ["11000"],
  "occupation": ["133"],
  "idempotency_key": "work24-collect-20260430-001"
}
```

#### Response 200
```json
{
  "job_code": "WORK24_COLLECT",
  "status": "BLOCKED",
  "run_id": 1,
  "collected_count": 0,
  "inserted_count": 0,
  "updated_count": 0,
  "skipped_count": 1,
  "failed_count": 0,
  "error_code": "JOB_SOURCE_001",
  "error_message": "WORK24 채용정보 API는 일반 사용자 제한으로 현재 사용할 수 없는 수집원입니다.",
  "started_at": "2026-04-30T00:00:00Z",
  "ended_at": "2026-04-30T00:00:02Z"
}
```

#### Notes
- 관리자 권한(`ADMIN`)이 필요하다.
- Work24 수집원이 비활성/보류 상태인 경우 외부 API 호출 없이 `JOB_SOURCE_001` + `BLOCKED` 배치 결과를 기록한다.
- Work24 인증키가 설정되지 않은 경우 `JOB_005`로 응답한다.
- Work24 외부 응답에 `errorCode`, `resultCode`, `code`, `resultMsg`, `message`류 오류 필드가 있으면 정상 채용공고로 파싱하지 않는다.
- 인증키 값은 요청/응답/문서에 포함하지 않는다.

## 채용공고 조회

### GET /jobs
DB에 저장된 `job_postings`만 조회한다. 프론트엔드는 ALIO 외부 API를 직접
호출하지 않고 이 API만 사용한다.

#### Query
```http
source=ALIO
keyword=python
location_code=R3010
employment_type_code=R1010
education_code=R7040
career_level_code=R2010
status=OPEN
page=1
size=20
```

#### Response 200
```json
{
  "items": [
    {
      "job_id": 1,
      "source": "ALIO",
      "source_job_id": "12345",
      "source_url": "https://job.alio.go.kr/recruitview.do?idx=12345",
      "company_name": "한국공공기관",
      "title": "AI 개발자 채용",
      "location": "서울",
      "location_code": "R3010",
      "career_level": "신입",
      "career_level_code": "R2010",
      "education": "대졸(2~3년)",
      "education_code": "R7040",
      "employment_type": "정규직",
      "employment_type_code": "R1010",
      "ncs_category": "정보통신",
      "ncs_category_code": "R6000",
      "organization_type": "기타공공기관",
      "organization_type_code": "A2005",
      "organization_category": "공공기관",
      "organization_category_code": "INST_CLSF",
      "ministry": "기획재정부",
      "ministry_code": "A1000",
      "posted_at": "2026-04-30T00:00:00Z",
      "deadline": "2026-05-10T00:00:00Z",
      "status": "OPEN",
      "collected_at": "2026-04-30T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

## 채용공고 저장 구조

- `job_postings`는 삭제하지 않고 ALIO, WORK24, SARAMIN, MANUAL 등 출처 확장형으로 재사용한다.
- `source + source_job_id`는 유니크 제약으로 중복 수집을 방지한다.
- `job_sources`는 채용공고 수집원의 상태를 관리한다.
- 초기 상태는 `ALIO=ACTIVE`, `WORK24=PENDING_APPROVAL`, `SARAMIN=DISABLED`, `MANUAL=ACTIVE`다.
- `ACTIVE`가 아닌 수집원은 외부 API 호출 전에 차단되고 `batch_job_runs.status=BLOCKED`로 기록된다.
- ALIO 코드 정의서 기준 공통코드 관리를 위해 `common_code_groups`, `common_codes`를 추가한다.
- 주요 코드 그룹: `R1000`, `R2000`, `R3000`, `R6000`, `R7000`, `ATCH_TYPE`, `A2000`, `INST_CLSF`, `A1000`.
- `batch_job_runs`는 ALIO 수집, 코드 동기화, 마감 동기화, 임베딩 배치까지 추적할 수 있게 `source`, `success_count`를 포함한다.
- 배치 `job_code` 예시는 `ALIO_RECRUIT_COLLECT`, `ALIO_RECRUIT_DETAIL_COLLECT`, `ALIO_CODE_SYNC`, `WORK24_COLLECT_DISABLED`, `JOB_CLOSE_SYNC`, `JOB_EMBEDDING`이다.
