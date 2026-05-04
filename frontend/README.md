# JobFit AI Frontend

Next.js 기반 JobFit AI 프론트엔드 애플리케이션이다.

## 현재 스택

- React 19
- TypeScript
- Next.js 16 App Router
- Tailwind CSS v4
- axios
- TanStack Query
- React Hook Form
- Zod
- shadcn/ui 스타일 컴포넌트

## 구현 상태

- 로그인/회원가입 화면 구현
- `/auth/login`, `/auth/signup`, `/auth/me`, `/auth/logout` API 연결
- Access Token localStorage 저장 및 요청 헤더 자동 주입
- Refresh Token HttpOnly Cookie 요청을 위한 `withCredentials: true` 설정
- Next.js App Router 기반 사용자/관리자 보호 라우트 구성
- TanStack Query `QueryClientProvider` 구성
- 로그인/회원가입 폼에 React Hook Form + Zod 검증 적용
- shadcn/ui 패턴 기반 `Button`, `Input`, `Alert` 컴포넌트 추가
- 사용자 대시보드, 이력서, 채용공고, 매칭 화면 mock UI 구현
- 관리자 대시보드, 카테고리, Q&A 게시글 화면 mock UI 구현
- 백엔드 공통 에러 응답 `{ code, message, details }` 타입 반영

## 실행

```powershell
npm install
npm run dev
```

기본 API 주소는 `http://localhost:8000`이다.
다른 백엔드 주소를 사용할 때는 `.env`에 아래 값을 설정한다.

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Next.js 개발 서버 기본 포트는 `3000`이다. 백엔드 `.env.example`의 CORS 기본 예시는 Next.js 기본 포트와 기존 Vite 포트를 함께 포함한다.

## 검증

```powershell
npm run lint
npm run build
```

## 다음 작업

- toast와 field error 표시 방식 고도화
- 이력서 업로드/파싱 화면 실제 API 연결
- AI 매칭 결과 화면 실제 API 연결
