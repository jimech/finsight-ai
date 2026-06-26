from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import analytics, auth, chat, evaluations, plans, profile, transactions, uploads

app = FastAPI(title="FinSight API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(uploads.router)
app.include_router(analytics.router)
app.include_router(transactions.router)
app.include_router(chat.router)
app.include_router(plans.router)
app.include_router(evaluations.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "finsight-api"}
