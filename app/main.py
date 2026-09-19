"""
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Swagger docs: http://localhost:8000/docs
ReDoc:        http://localhost:8000/redoc
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist (use Alembic migrations for real production rollouts)
    init_db()
    yield
    # Shutdown: nothing to clean up currently


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A modular backend for managing students, courses, and enrollments, "
        "with an integrated LangGraph + Gemini chatbot for natural-language "
        "querying of the student database."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
def root():
    """Root health-check endpoint."""
    return {
        "service": settings.APP_NAME,
        "status": "ok",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["Health"])
def health():
    """Liveness/readiness probe for container orchestration."""
    return {"status": "healthy"}
