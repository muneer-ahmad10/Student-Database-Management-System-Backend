"""
Centralized application configuration.

All environment-driven settings live here so the rest of the codebase
never touches `os.environ` directly. This keeps configuration modular
and easy to override per-environment (dev / test / staging / prod).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    APP_NAME: str = "Student Database Management System"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./student_management.db"

    # --- Gemini / LangGraph chatbot ---
    GOOGLE_API_KEY: str = ""
    GEMINI_CHAT_MODEL: str = "gemini-1.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    # --- Vector store (Chroma) ---
    CHROMA_PERSIST_DIR: str = "./chroma_store"
    CHROMA_COLLECTION_NAME: str = "student_profiles"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — avoids re-parsing the .env file on every import."""
    return Settings()


settings = get_settings()
