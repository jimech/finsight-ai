# FinSight AI — Production Deployment Guide

This guide prepares FinSight AI for deployment with:

- **Frontend:** [Vercel](https://vercel.com/) (Next.js)
- **Backend:** [Render](https://render.com/) (FastAPI) or a similar Python host
- **Database:** Managed PostgreSQL with **pgvector** support
- **Redis:** optional — not required for the MVP

> Do not deploy until you have created accounts and set environment variables. This document describes configuration only.

## Architecture overview

```
Browser → Vercel (Next.js) → Render (FastAPI) → PostgreSQL (pgvector)
                ↓
            Clerk (auth)
                ↓
            OpenAI (optional AI + embeddings)
```

The frontend calls the API using `NEXT_PUBLIC_API_URL`. The API verifies Clerk JWTs and allows CORS only from configured frontend origins (no wildcard `*`).

---

## Backend-only phase (current)

You can deploy and use the API **without a frontend**:

| Component | Status |
|-----------|--------|
| Supabase Postgres + pgvector | Required |
| Render FastAPI | Required |
| Vercel frontend | Optional — add when UI is ready |
| `FRONTEND_URL` on Render | `http://localhost:3000` until frontend exists |

**Production API:** `https://finsight-ai-bse9.onrender.com`

Verify after deploy:

```bash
chmod +x scripts/smoke-test-api.sh
./scripts/smoke-test-api.sh https://finsight-ai-bse9.onrender.com
```

When a new frontend is ready, see [frontend-integration.md](frontend-integration.md) and update `FRONTEND_URL` + Clerk redirect URLs.

---

## Pre-deployment checks

Run these locally before deploying:

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

### Frontend

```bash
cd apps/web
npm install
npm run build
```

### API health (local)

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok","service":"finsight-api"}
```

---

## 1. PostgreSQL with pgvector

FinSight uses the `pgvector` extension for transaction embeddings and semantic search.

### Provider options

| Provider | pgvector | Notes |
|----------|----------|-------|
| [Neon](https://neon.tech/) | Yes | Enable `vector` extension in SQL editor |
| [Supabase](https://supabase.com/) | Yes | Enable extension in Database → Extensions |
| [Railway](https://railway.app/) | Yes | Use Postgres template with pgvector |
| Render Postgres | Check plan | Standard Render Postgres may not include pgvector; prefer Neon/Supabase if embeddings are required |

### After creating the database

1. Copy the **connection string** (`DATABASE_URL`). Render and others often provide `postgresql://` — the API accepts both `postgresql://` and `postgresql+psycopg://`.
2. Run migrations (see [Running Alembic migrations](#5-running-alembic-migrations)). The migration `c8f1a2b3d4e5` runs `CREATE EXTENSION IF NOT EXISTS vector`.

### Embeddings without pgvector

If pgvector is unavailable, set `EMBEDDINGS_ENABLED=false`. Search and coach still work with deterministic fake embeddings for development-style behavior.

---

## 2. Render backend setup

### Create a Web Service

1. Connect your GitHub repository.
2. **Root directory:** `apps/api`
3. **Runtime:** Python 3.11+
4. **Build command:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Start command:**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

   Render sets `$PORT` automatically. Do not hardcode port `8000` in production.

### Backend environment variables (Render)

Set these in the Render service **Environment** tab:

| Variable | Required | Example / notes |
|----------|----------|----------------|
| `DATABASE_URL` | Yes | `postgresql://user:pass@host/db` from your managed Postgres |
| `FRONTEND_URL` | Yes | `https://your-app.vercel.app` (exact origin, no trailing slash) |
| `CLERK_SECRET_KEY` | Yes | Clerk secret key (`sk_live_...` or `sk_test_...`) |
| `CLERK_JWKS_URL` | Yes | `https://<clerk-domain>/.well-known/jwks.json` |
| `OPENAI_API_KEY` | For AI | OpenAI API key |
| `OPENAI_MODEL` | No | Default: `gpt-4.1-mini` |
| `AI_ENABLED` | No | `true` to enable coach/plan LLM personalization |
| `EMBEDDING_MODEL` | No | Default: `text-embedding-3-small` |
| `EMBEDDINGS_ENABLED` | No | `true` when pgvector + OpenAI embeddings are configured |

**Do not** set `NEXT_PUBLIC_*` variables on Render — those belong on Vercel.

### CORS

The API allows:

- `http://localhost:3000` and `http://localhost:3001` (local development)
- `FRONTEND_URL` (production frontend)

Wildcard origins (`*`) are **not** used.

### Verify backend after deploy

```bash
curl https://your-api.onrender.com/health
```

---

## 3. Vercel frontend setup

### Create a project

1. Import the repository on [Vercel](https://vercel.com/).
2. **Root directory:** `apps/web`
3. **Framework preset:** Next.js
4. **Build command:** `npm run build` (default)
5. **Install command:** `npm install` (default)

### Frontend environment variables (Vercel)

| Variable | Required | Example / notes |
|----------|----------|----------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Yes | `pk_live_...` or `pk_test_...` |
| `CLERK_SECRET_KEY` | Yes | Server-only; required for Clerk Next.js components |
| `NEXT_PUBLIC_API_URL` | Yes | `https://your-api.onrender.com` (no trailing slash) |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | No | `/sign-in` |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | No | `/sign-up` |

Copy the template from [`apps/web/.env.example`](../apps/web/.env.example).

**Never** expose `OPENAI_API_KEY`, `DATABASE_URL`, or `CLERK_JWKS_URL` to the frontend.

### Redeploy

After changing environment variables, trigger a new Vercel deployment. Set `FRONTEND_URL` on Render to match your Vercel production URL (including `https://`).

---

## 4. Clerk configuration

1. Create an application at [clerk.com](https://clerk.com/).
2. Add **allowed origins** / **domains** for:
   - `http://localhost:3000` (local)
   - Your Vercel production URL (e.g. `https://finsight.vercel.app`)
3. Configure sign-in and sign-up paths to match:
   - `/sign-in`
   - `/sign-up`
4. Copy keys to the correct services:
   - **Vercel:** `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`
   - **Render:** `CLERK_SECRET_KEY`, `CLERK_JWKS_URL`

Clerk JWTs are verified by the FastAPI backend on protected routes (`/auth/me`, `/profile`, `/uploads`, etc.).

---

## 5. OpenAI configuration

Optional but recommended for the full demo:

| Variable | Where | Purpose |
|----------|-------|---------|
| `OPENAI_API_KEY` | Render only | Coach chat and plan personalization |
| `OPENAI_MODEL` | Render only | e.g. `gpt-4.1-mini` |
| `AI_ENABLED` | Render only | `true` to enable LLM responses |
| `EMBEDDING_MODEL` | Render only | e.g. `text-embedding-3-small` |
| `EMBEDDINGS_ENABLED` | Render only | `true` for real vector search (requires pgvector) |

With `AI_ENABLED=false`, deterministic fallbacks still return useful coach and plan output for portfolio demos.

---

## 6. Running Alembic migrations

Run migrations against your **production** database before or immediately after the first backend deploy.

From your machine (with production `DATABASE_URL`):

```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql://..."   # your managed Postgres URL
alembic upgrade head
```

Alternatively, use Render's **Shell** or a one-off job with the same command.

This applies all migrations including pgvector and `transaction_embeddings`.

---

## 7. Production demo flow

After frontend and backend are live:

1. Open your Vercel URL and **sign up**
2. **Complete onboarding** at `/onboarding`
3. **Upload** [`demo-data/sample-transactions.csv`](../demo-data/sample-transactions.csv) at `/transactions/upload`
4. **View dashboard** — spending summary, recurring expenses, savings opportunities
5. **Generate embeddings** at `/transactions/search` (if `EMBEDDINGS_ENABLED=true`)
6. **Search transactions** — e.g. `coffee spending`
7. **Ask coach** at `/coach`
8. **Create monthly plan** at `/plan`
9. **Review AI runs** at `/admin/ai-runs`

> **Portfolio demo notice:** FinSight AI does not provide financial, tax, investment, credit, or legal advice.

---

## 8. Troubleshooting

| Issue | Check |
|-------|-------|
| CORS errors in browser | `FRONTEND_URL` on Render matches Vercel URL exactly (scheme + host, no trailing slash) |
| 401 on API calls | Clerk keys match between Vercel and Render; user is signed in |
| API unreachable from Vercel | `NEXT_PUBLIC_API_URL` points to Render URL; Render service is running |
| Migration fails on `vector` | Database provider supports pgvector; run `CREATE EXTENSION vector` manually if needed |
| Embeddings fail | `EMBEDDINGS_ENABLED=true` requires `OPENAI_API_KEY` and pgvector |
| Cold start delay (Render free tier) | First request may take 30–60s; health check may timeout briefly |

---

## 9. What this guide does not cover

- Actual deployment clicks (intentionally — configure first, deploy when ready)
- Docker production hosting
- CI/CD pipelines
- Sentry, Langfuse, or other observability tools
- Redis (optional, not required for MVP)

For local development, see the [root README](../README.md) and [apps/api/README.md](../apps/api/README.md).
