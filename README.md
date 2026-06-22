# FinSight AI

Your AI-powered personal finance coach — a full-stack portfolio project with a Next.js frontend and FastAPI backend.

## Repository structure

```
finsight-ai/
├── apps/
│   ├── web/          # Next.js + TypeScript + Tailwind
│   └── api/          # FastAPI (Python)
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

## Development notes

- **Auth** (Clerk) and **AI** (OpenAI) are planned but not implemented in this ticket.
- Database models, migrations, and dashboard pages are not included yet.
- See [docs/project-context.md](docs/project-context.md) for architecture and scope details.

## Stopping services

```bash
docker compose down
```

To remove named volumes as well:

```bash
docker compose down -v
```
