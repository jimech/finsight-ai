# FinSight API

FastAPI backend for FinSight AI.

## Prerequisites

- Python 3.11+
- PostgreSQL (via Docker Compose or local install)

## Setup

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy the repo root `.env.example` to `.env` and set:

```
DATABASE_URL=postgresql+psycopg://finsight:finsight_password@localhost:5432/finsight_db
CLERK_SECRET_KEY=sk_test_...
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
```

Both `postgresql://` and `postgresql+psycopg://` URLs are supported; the latter is recommended with psycopg3.

Start Postgres from the repo root:

```bash
docker compose up -d postgres
```

## Database migrations

Run all commands from `apps/api` with the virtual environment active.

Apply existing migrations:

```bash
alembic upgrade head
```

Generate a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

Verify tables:

```bash
docker compose exec postgres psql -U finsight -d finsight_db -c "\dt"
```

Expected tables: `users`, `uploaded_files`, `transactions`, `chat_messages`, `ai_runs`, `evaluations`.

## Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"finsight-api"}
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Authentication

Protected routes use `get_current_user` or `get_current_db_user` from `app/core/auth.py`. `get_current_db_user` verifies the Clerk JWT and ensures a matching row exists in `users` (synced via `get_or_create_user_from_auth`).

```bash
# Public
curl http://localhost:8000/health

# Protected — returns 401 without a valid Clerk session token
curl -i http://localhost:8000/auth/me
# Protected — creates local user on first call, returns user_id + email
curl -H "Authorization: Bearer <token>" http://localhost:8000/auth/me
```

## Project layout

```
apps/api/
├── alembic/              # Alembic migrations
├── app/
│   ├── core/
│   │   ├── config.py     # Settings (DATABASE_URL, Clerk)
│   │   └── auth.py       # JWT auth + get_current_db_user
│   ├── services/users.py # get_or_create_user_from_auth
│   ├── routers/auth.py   # /auth/me
│   ├── db/               # SQLAlchemy base and session
│   ├── models/           # ORM models
│   └── main.py           # FastAPI app
├── alembic.ini
└── requirements.txt
```
