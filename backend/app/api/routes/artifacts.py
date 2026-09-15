import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.artifact import ArtifactResponse, ArtifactListResponse
from app.services.artifact_service import ArtifactService
from app.services.session_service import SessionService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an artifact by ID",
)
def get_artifact(
    artifact_id: uuid.UUID,
    session_id: Optional[uuid.UUID] = Query(None, description="Optional session scope to prevent cross-session access"),
    db: Session = Depends(get_db),
) -> ArtifactResponse:
    artifact = ArtifactService.get_artifact(db, artifact_id, session_id=session_id)
    return ArtifactResponse.model_validate(artifact)


@router.get(
    "/session/{session_id}",
    response_model=List[ArtifactResponse],
    status_code=status.HTTP_200_OK,
    summary="List all artifacts for a session",
)
def list_session_artifacts(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[ArtifactResponse]:
    # Ensure session exists
    SessionService.get_session(db, session_id)
    artifacts = ArtifactService.list_session_artifacts(db, session_id)
    return [ArtifactResponse.model_validate(a) for a in artifacts]


@router.delete(
    "/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an artifact",
)
def delete_artifact(
    artifact_id: uuid.UUID,
    session_id: Optional[uuid.UUID] = Query(None, description="Optional session scope to prevent cross-session deletion"),
    db: Session = Depends(get_db),
) -> None:
    ArtifactService.delete_artifact(db, artifact_id, session_id=session_id)
    db.commit()

