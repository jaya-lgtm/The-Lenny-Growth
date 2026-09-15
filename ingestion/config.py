import os
from pathlib import Path
from pydantic import BaseModel, Field


class IngestionConfig(BaseModel):
    """Configuration for transcript and article ingestion."""

    data_dir: Path = Field(
        default_factory=lambda: Path(
            os.environ.get("DATA_DIR", "data/transcripts")
        )
    )
    corpus_repo_url: str = Field(
        default_factory=lambda: os.environ.get(
            "CORPUS_REPO_URL", "https://github.com/ChatPRD/lennys-podcast-transcripts"
        )
    )
    chunk_size: int = Field(default=800, ge=100, le=4000)
    chunk_overlap: int = Field(default=150, ge=0, le=1000)
    embedding_provider: str = Field(
        default_factory=lambda: os.environ.get("EMBEDDING_PROVIDER", "ollama")
    )
    ollama_base_url: str = Field(
        default_factory=lambda: os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    ollama_embedding_model: str = Field(
        default_factory=lambda: os.environ.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    )
    batch_size: int = Field(default=10, ge=1, le=100)


def get_ingestion_config() -> IngestionConfig:
    return IngestionConfig()
