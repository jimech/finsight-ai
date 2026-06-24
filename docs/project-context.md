# FinSight AI Project Context

FinSight AI is an AI-powered personal finance coach.

MVP:
- User auth and onboarding
- CSV transaction upload
- Spending dashboard
- Deterministic financial analytics
- AI coach grounded in user transaction data
- Monthly savings plan
- AI evaluation and monitoring

Stack:
- Frontend: Next.js + TypeScript + Tailwind
- Backend: FastAPI + Python
- Database: PostgreSQL
- Vector search: pgvector
- Queue/cache: Redis
- Auth: Clerk
- AI: OpenAI Responses API
- Observability: app logs first, Langfuse later
- Deployment: Render, Railway, Fly.io, or similar

Rules:
- The LLM must not calculate financial totals directly.
- All user financial calculations must come from deterministic backend tools.
- All database queries must be scoped by user_id.
- AI responses about user spending must include citations.
- No investment, tax, legal, or credit advice in MVP.