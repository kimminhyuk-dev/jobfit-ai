# API_SPEC

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
