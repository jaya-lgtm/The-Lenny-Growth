import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db.session import get_db
from app.api.errors import make_error_response

logger = logging.getLogger("app.api.routes.health")
router = APIRouter()
settings = get_settings()


@router.get("/health", status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)):
    """Health check endpoint performing deep verification against the database."""
    try:
        # Perform real connectivity check
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.environment,
            "database": "connected",
        }
    except Exception as exc:
        logger.error("Health check database error: %s", str(exc), exc_info=True)
        return make_error_response(
            code="DATABASE_UNAVAILABLE",
            message="Database connectivity check failed.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"status": "degraded", "error": str(exc)},
        )
