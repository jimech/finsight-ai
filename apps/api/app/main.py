from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, profile, transactions, uploads

app = FastAPI(title="FinSight API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(uploads.router)
app.include_router(transactions.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "finsight-api"}
