# JobFit AI Frontend

Next.js frontend for JobFit AI.

## Stack

- Next.js 16 App Router
- React 19
- TypeScript
- Tailwind CSS v4
- TanStack Query
- React Hook Form
- Zod
- axios
- shadcn/ui-style local components

## Implemented Areas

- Auth provider and protected routes.
- Split login pages:
  - `/login`: normal user login.
  - `/company/login`: company/admin login.
- Role redirects:
  - ADMIN -> `/admin/dashboard`
  - COMPANY -> `/company/dashboard`
  - USER -> `/user/dashboard`
- User pages:
  - `/user/dashboard`
  - `/user/jobs`
  - `/user/jobs/[jobId]`
  - `/user/applications`
  - `/user/resumes`
  - `/user/profile`
- Company page:
  - `/company/dashboard`
  - `/company/jobs`
- Admin pages:
  - dashboard, jobs, users, categories, posts, mock jobs
- Global toast host for network/server errors.
- Resume interview practice UI on the resume page.
- Address and tech-stack profile inputs.
- Company job posting management for manual postings.
- Account recovery pages for personal and company email/password recovery.

## API Configuration

Default API URL:

```text
http://localhost:8000
```

Override with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The axios client uses `withCredentials: true` for refresh-token cookie flows.

## Run

```powershell
npm install
npm run dev
```

Default frontend dev server:

```text
http://localhost:3000
```

## Verify

```powershell
npm run lint
npm run build
```

## Known Gaps

- `/user/matches` still uses old mock matching stats.
- Full vector-based matching UI/API is planned but not implemented.
- Company self-signup is not implemented.
