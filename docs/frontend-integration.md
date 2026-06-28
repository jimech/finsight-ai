# Frontend integration guide

Use this document when wiring a new frontend (e.g. from Google AI Studio) to the **production FinSight API**.

## Production API

```text
Base URL: https://finsight-ai-bse9.onrender.com
Health:   https://finsight-ai-bse9.onrender.com/health
Docs:     https://finsight-ai-bse9.onrender.com/docs
```

Local development:

```text
Base URL: http://localhost:8000
```

---

## Authentication (Clerk)

All protected routes require a Clerk session JWT:

```http
Authorization: Bearer <clerk_session_token>
```

### How to get the token (JavaScript)

If using Clerk in a React/Next.js app:

```javascript
const token = await clerk.session.getToken();
```

Or with `@clerk/nextjs`:

```javascript
import { useAuth } from "@clerk/nextjs";

const { getToken } = useAuth();
const token = await getToken();
```

### First API call

`GET /auth/me` creates the local user row on first success.

```javascript
const response = await fetch("https://finsight-ai-bse9.onrender.com/auth/me", {
  headers: { Authorization: `Bearer ${token}` },
});
const user = await response.json();
```

### Clerk keys for the frontend

| Variable | Where |
|----------|-------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Frontend env |
| `CLERK_SECRET_KEY` | Server only (Next.js), never in browser |

Clerk development domain: `modern-seasnail-80.clerk.accounts.dev`

---

## Request pattern

```javascript
const API_URL = "https://finsight-ai-bse9.onrender.com";

async function apiRequest(path, token, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }

  return response.json();
}
```

CSV upload uses `multipart/form-data` (no `Content-Type: application/json`):

```javascript
const formData = new FormData();
formData.append("file", csvFile);

await fetch(`${API_URL}/uploads/transactions`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: formData,
});
```

---

## API endpoints

### Public

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/auth/me` | Yes | Current user; syncs Clerk user to DB |

### Profile

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/profile` | Yes | Get user profile |
| PUT | `/profile` | Yes | Update profile |

**PUT body example:**

```json
{
  "name": "Alex Demo",
  "monthly_income": 3500,
  "savings_goal": 500,
  "current_savings": 2000,
  "financial_priority": "save_money",
  "coaching_tone": "supportive"
}
```

`financial_priority`: `save_money` | `reduce_spending` | `pay_down_debt` | `build_emergency_fund` | `understand_spending`

`coaching_tone`: `supportive` | `direct` | `playful`

### Uploads

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/uploads/transactions` | Yes | Upload CSV (multipart file field: `file`) |
| GET | `/uploads` | Yes | List uploads |

**CSV columns:** `date`, `description`, `amount` (required); `merchant`, `category` (optional)

Demo file: [`demo-data/sample-transactions.csv`](../demo-data/sample-transactions.csv)

### Transactions

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/transactions` | Yes | List transactions (`?limit=50&offset=0`) |
| PATCH | `/transactions/{id}` | Yes | Update merchant/category |
| POST | `/transactions/embeddings/generate` | Yes | Generate search embeddings |
| POST | `/transactions/search` | Yes | Semantic search |

**Search body:**

```json
{ "query": "coffee spending", "top_k": 5 }
```

### Analytics (same `/transactions` prefix)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/transactions/summary` | Yes | Dashboard spending summary |
| GET | `/transactions/categories` | Yes | Category breakdown |
| GET | `/transactions/recurring` | Yes | Recurring expenses |
| GET | `/transactions/savings-opportunities` | Yes | Savings suggestions |

Optional query: `?start_date=2026-01-01&end_date=2026-03-31`

### AI coach

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/chat` | Yes | Send coach message |
| GET | `/chat/history` | Yes | Chat history |

**POST body:**

```json
{ "message": "Where can I cut spending this month?" }
```

Response includes `message`, `citations` (tools + transactions), `ai_run_id`.

Requires `AI_ENABLED=true` and `OPENAI_API_KEY` on Render for LLM responses. Deterministic fallbacks work when AI is disabled.

### Monthly plan

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/plans/monthly` | Yes | Generate monthly action plan |

**Body (optional):**

```json
{ "start_date": "2026-01-01", "end_date": "2026-03-31" }
```

### AI runs & evaluations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/ai-runs` | Yes | List AI runs |
| GET | `/admin/evaluations` | Yes | List evaluations |
| POST | `/admin/evaluate/{ai_run_id}` | Yes | Submit evaluation scores |

---

## Recommended user flow (wire in this order)

1. Sign in with Clerk
2. `GET /auth/me`
3. `PUT /profile` (onboarding)
4. `POST /uploads/transactions` (demo CSV)
5. `GET /transactions/summary` (dashboard)
6. `POST /transactions/embeddings/generate`
7. `POST /transactions/search`
8. `POST /chat`
9. `POST /plans/monthly`
10. `GET /admin/ai-runs`

---

## CORS (when frontend is deployed)

The API allows:

- `http://localhost:3000`
- `http://localhost:3001`
- `FRONTEND_URL` (set on Render)

When your new frontend has a live URL:

1. Render → Environment → set `FRONTEND_URL=https://your-frontend-url.com`
2. Clerk → Allowed redirect URLs → add your frontend URL
3. Redeploy Render (automatic on env change)

---

## Backend env vars (Render)

| Variable | Current recommendation |
|----------|------------------------|
| `DATABASE_URL` | Supabase session pooler URL |
| `FRONTEND_URL` | `http://localhost:3000` until frontend is deployed |
| `CLERK_SECRET_KEY` | From Clerk API keys |
| `CLERK_JWKS_URL` | `https://modern-seasnail-80.clerk.accounts.dev/.well-known/jwks.json` |
| `AI_ENABLED` | `false` initially, then `true` |
| `EMBEDDINGS_ENABLED` | `false` initially, then `true` |
| `OPENAI_API_KEY` | Required when AI/embeddings enabled |

---

## Enable AI later (Render dashboard)

When ready to test coach and embeddings in production:

1. Add `OPENAI_API_KEY` on Render
2. Set `AI_ENABLED=true`
3. Set `EMBEDDINGS_ENABLED=true` (requires pgvector on Supabase — already set up)
4. Redeploy

---

## Reference implementation

The existing Next.js client in `apps/web/src/lib/api.ts` implements all endpoints above. When integrating a new frontend, use it as a reference for paths, request bodies, and response types.

---

## Portfolio notice

FinSight AI is a demo project. It does not provide financial, tax, investment, credit, or legal advice.
