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

Copy the repo root `.env.example` to `.env` and set `DATABASE_URL`:

```
DATABASE_URL=postgresql+psycopg://finsight:finsight_password@localhost:5432/finsight_db
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

## Project layout

```
apps/api/
├── alembic/              # Alembic migrations
├── app/
│   ├── core/config.py    # Settings (DATABASE_URL)
│   ├── db/               # SQLAlchemy base and session
│   ├── models/           # ORM models
│   └── main.py           # FastAPI app
├── alembic.ini
└── requirements.txt
```
