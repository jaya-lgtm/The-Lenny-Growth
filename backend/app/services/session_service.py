from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.models.session import SessionModel
from app.schemas.session import SessionCreate, SessionUpdate
from app.api.errors import SessionNotFoundException


class SessionService:
    @staticmethod
    def create_session(db: Session, session_in: SessionCreate) -> SessionModel:
        now = datetime.now(timezone.utc)
        session = SessionModel(
            id=uuid.uuid4(),
            title=session_in.title or "New Conversation",
            user_metadata=session_in.user_metadata,
            created_at=now,
            updated_at=now,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def list_sessions(db: Session) -> List[SessionModel]:
        stmt = select(SessionModel).order_by(
            desc(SessionModel.updated_at), desc(SessionModel.created_at)
        )
        sessions = list(db.scalars(stmt).all())

        # Auto-heal any session that currently has the default placeholder title and has user messages
        from app.models.message import MessageModel
        from app.services.title_generator import generate_session_title

        needs_commit = False
        for s in sessions:
            if not s.title or s.title.strip() == "New Conversation" or s.title.startswith("New Conversation"):
                first_msg = (
                    db.query(MessageModel)
                    .filter(MessageModel.session_id == s.id, MessageModel.role == "user")
                    .order_by(MessageModel.created_at.asc())
                    .first()
                )
                if first_msg and first_msg.content:
                    s.title = generate_session_title(first_msg.content)
                    needs_commit = True

        if needs_commit:
            try:
                db.commit()
            except Exception:
                db.rollback()

        return sessions

    @staticmethod
    def get_session(db: Session, session_id: uuid.UUID) -> SessionModel:
        session = db.get(SessionModel, session_id)
        if not session:
            raise SessionNotFoundException(session_id)
        return session

    @staticmethod
    def update_session(
        db: Session, session_id: uuid.UUID, session_in: SessionUpdate
    ) -> SessionModel:
        session = SessionService.get_session(db, session_id)
        session.title = session_in.title
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete_session(db: Session, session_id: uuid.UUID) -> None:
        session = SessionService.get_session(db, session_id)
        db.delete(session)
        db.commit()
