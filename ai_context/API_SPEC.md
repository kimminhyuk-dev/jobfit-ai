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
