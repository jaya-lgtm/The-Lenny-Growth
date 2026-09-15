import uuid
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.artifact import ArtifactModel
from app.schemas.artifact import ArtifactCreate
from app.api.errors import AppException

logger = logging.getLogger("backend.services.artifact")


class ArtifactNotFoundException(AppException):
    def __init__(self, artifact_id: uuid.UUID):
        super().__init__(
            code="ARTIFACT_NOT_FOUND",
            message=f"Artifact with ID '{artifact_id}' was not found.",
            status_code=404,
        )


class CrossSessionAccessException(AppException):
    def __init__(self, artifact_id: uuid.UUID, session_id: uuid.UUID):
        super().__init__(
            code="CROSS_SESSION_ACCESS_DENIED",
            message=f"Access denied: Artifact '{artifact_id}' does not belong to session '{session_id}'.",
            status_code=403,
        )



class ArtifactService:
    @staticmethod
    def create_artifact(
        db: Session,
        session_id: uuid.UUID,
        artifact_in: ArtifactCreate,
        message_id: Optional[uuid.UUID] = None,
    ) -> ArtifactModel:
        """
        Persists a new immutable growth artifact.
        """
        artifact = ArtifactModel(
            id=uuid.uuid4(),
            session_id=session_id,
            message_id=message_id or artifact_in.message_id,
            artifact_type=artifact_in.artifact_type,
            content_format=artifact_in.content_format,
            schema_version=artifact_in.schema_version,
            title=artifact_in.title,
            content=artifact_in.content,
            artifact_metadata=artifact_in.artifact_metadata or {},
        )
        db.add(artifact)
        db.flush()
        db.refresh(artifact)
        logger.info(f"Created artifact {artifact.id} of type '{artifact.artifact_type}' in session {session_id}")
        return artifact

    @staticmethod
    def get_artifact(
        db: Session,
        artifact_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
    ) -> ArtifactModel:
        artifact = db.get(ArtifactModel, artifact_id)
        if not artifact:
            raise ArtifactNotFoundException(artifact_id)
        if session_id and artifact.session_id != session_id:
            raise CrossSessionAccessException(artifact_id, session_id)
        return artifact

    @staticmethod
    def list_session_artifacts(db: Session, session_id: uuid.UUID) -> List[ArtifactModel]:
        stmt = (
            select(ArtifactModel)
            .where(ArtifactModel.session_id == session_id)
            .order_by(ArtifactModel.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def delete_artifact(
        db: Session,
        artifact_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
    ) -> None:
        artifact = ArtifactService.get_artifact(db, artifact_id, session_id=session_id)
        db.delete(artifact)
        db.flush()
        logger.info(f"Deleted artifact {artifact_id}")

