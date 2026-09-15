import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from ingestion.pipeline import IngestionPipeline
from ingestion.config import get_ingestion_config

logger = logging.getLogger("backend.api.ingest")
router = APIRouter(tags=["Ingestion"])


class IngestRequest(BaseModel):
    provider: Optional[str] = None
    force: bool = False
    clone: bool = False
    clean_demo: bool = True
    limit: Optional[int] = None


class IngestResponse(BaseModel):
    status: str
    discovered: int
    inserted: int
    skipped: int
    failed: int
    chunks_created: int
    cleaned_demo: int = 0
    elapsed_seconds: float = 0.0
    errors: list


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger knowledge base transcript ingestion",
)
def trigger_ingestion(
    req: Optional[IngestRequest] = None,
    db: Session = Depends(get_db),
) -> IngestResponse:
    """Scan transcript repository and index chunks with vector embeddings."""
    from ingestion.pipeline import clone_or_update_repo
    cfg = get_ingestion_config()
    force_reingest = False
    clean_demo = True
    limit = None

    if req:
        if req.provider:
            cfg.embedding_provider = req.provider
        force_reingest = req.force
        clean_demo = req.clean_demo
        limit = req.limit
        if req.clone:
            clone_or_update_repo(cfg.corpus_repo_url, cfg.data_dir)

    pipeline = IngestionPipeline(config=cfg)
    metrics = pipeline.run(
        db=db,
        force_reingest=force_reingest,
        clean_demo=clean_demo,
        limit=limit,
    )

    return IngestResponse(
        status="completed",
        discovered=metrics["discovered"],
        inserted=metrics["inserted"],
        skipped=metrics["skipped"],
        failed=metrics["failed"],
        chunks_created=metrics["chunks_created"],
        cleaned_demo=metrics.get("cleaned_demo", 0),
        elapsed_seconds=metrics.get("elapsed_seconds", 0.0),
        errors=metrics["errors"],
    )
