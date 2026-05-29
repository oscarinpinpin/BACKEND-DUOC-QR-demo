import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine

app = FastAPI(title="API QR", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/qr_duoc"
)
engine = create_engine(DATABASE_URL)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"service": "api-qr", "status": "ok"}
