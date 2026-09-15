import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parent.parent.parent / ".env"),
            str(Path(__file__).resolve().parent.parent / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "The Lenny Growth Assistant"
    environment: str = "development"

    # PostgreSQL configuration
    postgres_db: str = "lenny_growth"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_port: int = 5432

    # Database URLs
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@db:5432/lenny_growth"
    )
    test_database_url: str = (
        "postgresql+psycopg2://postgres:postgres@db:5432/lenny_growth_test"
    )

    # Server settings
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 5173
    vite_backend_url: str = "http://backend:8000"

    # Embedding & Retrieval Settings (Milestone 2)
    embedding_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    retrieval_top_k: int = 5
    retrieval_similarity_threshold: Optional[float] = None
    data_dir: str = "data/transcripts"
    chunk_size: int = 800
    chunk_overlap: int = 150

    # LLM Provider Settings (Milestone 2)
    llm_provider: str = "ollama"
    ollama_model: str = "llama3.1:8b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    llm_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
