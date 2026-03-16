# Deployment Plan (Portfolio MVP)

This document is optimized for a solo-project deploy that is cheap, clear, and
easy to explain in interviews.

## 1. Production readiness review

Current strengths:

- modular backend architecture (routes/services/repositories)
- migrations and schema history managed with Alembic
- standardized API error payloads and request IDs
- audit logging for sensitive actions
- practical automated tests for API, integration flows, and validation

Known production gaps (intentional for MVP):

- demo-role header auth instead of real user authentication
- in-memory rate limiter (single-instance only)
- no background jobs/queue
- no distributed cache

## 2. Environment separation guidance

Use 3 environment profiles:

- `local`: Docker Compose, hot reload, debug enabled
- `staging`: production-like settings with test/demo data
- `production`: locked CORS, debug off, managed Postgres

Key backend variables:

- `ND_ENVIRONMENT`
- `ND_DEBUG`
- `ND_LOG_LEVEL`
- `ND_DATABASE_URL` (preferred in hosted envs)
- `ND_CORS_ORIGINS`
- `ND_RATE_LIMIT_ENABLED`
- `ND_RATE_LIMIT_WINDOW_SECONDS`
- `ND_RATE_LIMIT_MAX_WRITE_REQUESTS`

Frontend variable:

- `VITE_API_URL` (must point to deployed backend base URL)

## 3. Deployment configuration suggestions

Backend:

- run `alembic upgrade head` as a release/pre-start command
- run app with a single `uvicorn` process for MVP simplicity
- keep health endpoint public (`/api/v1/health`) for platform checks
- set `ND_DEBUG=false` outside local

Database:

- use managed PostgreSQL
- enforce separate DBs for staging and production
- enable automated backups at host level

Frontend:

- build with `npm run build`
- deploy static assets on a CDN-capable frontend host
- keep API base URL in per-environment variables

## 4. Hosting options (backend / DB / frontend)

Backend hosting options:

- Render Web Service: simple deploy UX, easy Python support
  - https://render.com/docs
  - https://render.com/pricing
- Railway Service: fast deploy flow, good for portfolio MVPs
  - https://docs.railway.com
  - https://railway.com/pricing
- Fly.io Apps: VM-based control and global deployment options
  - https://fly.io/docs
  - https://fly.io/pricing

Database hosting options:

- Supabase Postgres: managed Postgres with backups/options
  - https://supabase.com/pricing
- Render PostgreSQL: same-vendor simplicity with Render backend
  - https://render.com/docs/postgresql
  - https://render.com/pricing
- Railway PostgreSQL: same-vendor simplicity with Railway backend
  - https://docs.railway.com/reference/databases
  - https://railway.com/pricing

Frontend hosting options:

- Vercel (Hobby/Pro): strong DX for Vite/React static deploys
  - https://vercel.com/docs
  - https://vercel.com/pricing
- Netlify: straightforward static hosting and previews
  - https://docs.netlify.com
  - https://www.netlify.com/pricing
- Cloudflare Pages: global edge delivery for static frontend
  - https://developers.cloudflare.com/pages
  - https://www.cloudflare.com/plans/developer-platform/

## 5. Best low-cost deployment path for this project

Recommended path:

1. Frontend on Vercel.
2. Backend API on Railway (or Render if preferred UX).
3. PostgreSQL on the same backend vendor (Railway Postgres or Render Postgres).

Why this path:

- lowest setup complexity for one maintainer
- minimal cross-provider networking/debug overhead
- easy to explain in interviews

## 6. Minimal release checklist

1. Set production env vars (`ND_DEBUG=false`, production CORS, `ND_DATABASE_URL`).
2. Run backend tests: `python3 -m pytest`.
3. Run frontend build: `npm run build`.
4. Apply migrations on target DB: `alembic upgrade head`.
5. Smoke test:
   - `GET /api/v1/health`
   - login/demo role flow
   - create patient
   - create appointment
   - create linked visit
6. Tag release in Git and update README release note section.
