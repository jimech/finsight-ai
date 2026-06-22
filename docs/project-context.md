# FinSight AI — Project Context

## Overview

FinSight AI is a production-style portfolio project: an AI-powered personal finance coach. Users will eventually get guidance on budgeting, spending, and financial goals through a modern web app backed by a FastAPI service.

This document captures the intended architecture and scope for early development tickets.

## Monorepo Layout

```
finsight-ai/
├── apps/
│   ├── web/          # Next.js frontend (TypeScript, Tailwind)
│   └── api/          # FastAPI backend (Python)
├── docs/             # Project documentation
├── docker-compose.yml
└── .env.example
```

## Tech Stack

| Layer        | Technology              | Status        |
| ------------ | ----------------------- | ------------- |
| Frontend     | Next.js, TypeScript, Tailwind | Initialized |
| Backend      | FastAPI, Python         | Initialized   |
| Database     | PostgreSQL              | Docker only   |
| Cache/queue  | Redis                   | Docker only   |
| Auth         | Clerk                   | Planned       |
| AI           | OpenAI                  | Planned       |

## Current Scope (Ticket 0.1)

- Monorepo structure with runnable frontend and backend
- Docker Compose for local Postgres and Redis
- API health check at `GET /health`
- Minimal marketing-style home page on the frontend

## Out of Scope (for now)

- Authentication (Clerk)
- Database models and migrations
- AI integrations (OpenAI)
- File uploads
- Dashboard or authenticated app pages

## Local Ports

| Service   | Port |
| --------- | ---- |
| Web       | 3000 |
| API       | 8000 |
| Postgres  | 5432 |
| Redis     | 6379 |

## Environment Variables

See `.env.example` at the repository root. Copy it to `.env` and adjust values for local development.
