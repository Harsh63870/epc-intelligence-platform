"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.routes import router
from app.api.seed import router as seed_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="EPC Intelligence Platform API",
    description="AI-powered project intelligence for data centre EPC delivery",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(seed_router, prefix="/api/v1")


@app.get("/")
def root() -> dict:
    return {"service": "EPC Intelligence Platform API", "docs": "/docs"}
