# FinSight AI

Your AI-powered personal finance coach — a full-stack portfolio project with a Next.js frontend and FastAPI backend.

## Repository structure

```
finsight-ai/
├── apps/
│   ├── web/          # Next.js + TypeScript + Tailwind
│   └── api/          # FastAPI (Python)
├── demo-data/        # Sample CSV for portfolio demos
│   └── sample-transactions.csv
├── docs/
│   └── project-context.md
├── docker-compose.yml
└── .env.example
```

## Prerequisites

- [Node.js](https://nodejs.org/) 20+
- [Python](https://www.python.org/) 3.11+
- [Docker](https://www.docker.com/) and Docker Compose

## Setup

### 1. Clone and configure environment

```bash
git clone <repository-url>
cd finsight-ai
cp .env.example .env
```

Edit `.env` if you need different database credentials or ports.

### 2. Start Postgres and Redis

```bash
docker compose up -d
```

This starts:

- **Postgres** on `localhost:5432` (persistent volume: `postgres_data`)
- **Redis** on `localhost:6379` (persistent volume: `redis_data`)

Verify services are running:

```bash
docker compose ps
```

### 3. Run the API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"finsight-api"}
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Run the frontend

In a separate terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). You should see the FinSight AI home page.

## Demo data

FinSight includes a fake transaction dataset for portfolio reviewers and local testing.

**File:** [`demo-data/sample-transactions.csv`](demo-data/sample-transactions.csv)

- **100 transactions** across **3 months** (Jan–Mar 2026)
- Columns: `date`, `description`, `merchant`, `amount`, `category`
- All data is fictional — no real bank accounts, card numbers, or personal information
- Includes recurring charges (rent, utilities, Netflix, Spotify, gym)
- Includes discretionary spending patterns (coffee, dining, shopping) that surface savings opportunities in the dashboard

### How to use the sample CSV

1. Sign in at [http://localhost:3000](http://localhost:3000) (or create an account).
2. Go to **Upload transactions** (`/transactions/upload`).
3. Select `demo-data/sample-transactions.csv` from this repository and upload it.
4. Open the **Dashboard** to see spending summary, category breakdown, recurring expenses, and savings opportunities.

You can also copy the CSV snippet from the landing page or upload page if you prefer.

### Recommended demo flow

1. **Sign up** — create a Clerk account at `/sign-up`
2. **Complete onboarding** — add income, savings goal, and coaching preferences at `/onboarding`
3. **Upload sample CSV** — import `demo-data/sample-transactions.csv`
4. **View dashboard** — review income, spending, categories, recurring expenses, and savings opportunities
5. **Generate embeddings** — on `/transactions/search`, click **Generate embeddings**
6. **Search transactions** — try queries like `coffee spending` or `subscription charges`
7. **Ask coach** — open `/coach` and ask about saving money or recurring expenses
8. **Create monthly plan** — open `/plan` for a deterministic savings action plan
9. **Review AI runs** — open `/admin/ai-runs` to inspect outputs and record evaluations

> **Portfolio demo notice:** FinSight AI is a portfolio project for demonstration purposes. It does not provide financial, tax, investment, credit, or legal advice. Spending totals and plans come from deterministic backend analytics; AI coach answers cite those tools and retrieved transaction snippets.

## Development notes

- **AI coach** and **monthly plan** use OpenAI when `AI_ENABLED=true` and `OPENAI_API_KEY` is set; deterministic fallbacks work without AI.
- Clerk users are synced to the local `users` table on first `GET /auth/me` call.
- See [docs/project-context.md](docs/project-context.md) for architecture and scope details.

## Authentication (Clerk)

FinSight uses [Clerk](https://clerk.com/) for auth. The frontend protects `/dashboard` via `proxy.ts`; the API verifies Clerk JWTs for protected routes like `GET /auth/me`.

### 1. Create a Clerk application

1. Sign up at [clerk.com](https://clerk.com/) and create an application.
2. From the Clerk Dashboard, copy:
   - **Publishable key** → `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - **Secret key** → `CLERK_SECRET_KEY` (server only — never expose to the browser)
   - **JWKS URL** (API Keys → Advanced) → `CLERK_JWKS_URL`

### 2. Configure environment variables

**Repo root `.env`** (used by the API):

```bash
CLERK_SECRET_KEY=sk_test_...
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
```

**`apps/web/.env.local`** (used by Next.js — copy from `apps/web/.env.example`):

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
```

> `CLERK_SECRET_KEY` is required in `apps/web/.env.local` for server-side Clerk components. Only `NEXT_PUBLIC_*` keys are sent to the browser.

### 3. Verify auth

| Route | Auth required | Expected |
|-------|---------------|----------|
| `GET /` | No | Public landing page |
| `GET /dashboard` | Yes | Redirects to sign-in when signed out |
| `GET /health` | No | `{"status":"ok","service":"finsight-api"}` |
| `GET /auth/me` | Yes (Bearer token) | 401 without token; user info with valid Clerk JWT |

Test the API (no token → 401):

```bash
curl -i http://localhost:8000/auth/me
```

With a Clerk session token from the browser (signed in → DevTools → Network → copy `Authorization` header or use Clerk's `getToken()`), call:

```bash
curl -H "Authorization: Bearer <clerk_session_token>" http://localhost:8000/auth/me
```

## Database setup

The API uses SQLAlchemy 2.x with Alembic migrations against PostgreSQL.

### 1. Ensure Postgres is running

```bash
docker compose up -d postgres
```

### 2. Install API dependencies

```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt
```

Set `DATABASE_URL` in the repo root `.env` (see `.env.example`):

```
DATABASE_URL=postgresql+psycopg://finsight:finsight_password@localhost:5432/finsight_db
```

See [apps/api/README.md](apps/api/README.md) for backend-specific setup.

### 3. Create and apply migrations

From `apps/api`:

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head
```

The initial migration creates: `users`, `uploaded_files`, `transactions`, `chat_messages`, `ai_runs`, and `evaluations`.

### 4. Verify tables

```bash
docker compose exec postgres psql -U finsight -d finsight_db -c "\dt"
```

## Stopping services

```bash
docker compose down
```

To remove named volumes as well:

```bash
docker compose down -v
```
