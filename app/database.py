"""
Database engine, session factory, and declarative base.

Using SQLAlchemy 2.0 style. DATABASE_URL is swappable via env var, so the
same codebase runs on SQLite for local dev and Postgres/MySQL in production.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and guarantees cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Called on app startup (use Alembic migrations in real prod)."""
    # Import models so they are registered on Base.metadata before create_all
    from app.models import student, course, enrollment  # noqa: F401

    Base.metadata.create_all(bind=engine)
