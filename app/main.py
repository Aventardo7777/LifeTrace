"""LifeTrace FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME, APP_SUBTITLE, APP_VERSION, STATIC_DIR
from .database import SessionLocal, init_db
from .routers import analysis, dashboard, io, records
from .seed import ensure_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        ensure_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=APP_NAME,
    description=APP_SUBTITLE,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(dashboard.router)
app.include_router(records.router)
app.include_router(analysis.router)
app.include_router(io.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION}
