from datetime import datetime, timezone
import uuid
from typing import List
from sqlalchemy import select, asc
from sqlalchemy.orm import Session
from app.models.message import MessageModel
from app.schemas.message import MessageCreate
from app.services.session_service import SessionService


class MessageService:
    @staticmethod
    def create_message(
        db: Session, session_id: uuid.UUID, message_in: MessageCreate
    ) -> MessageModel:
        # Verify that parent session exists (raises SessionNotFoundException if not)
        session = SessionService.get_session(db, session_id)

        now = datetime.now(timezone.utc)
        message = MessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role=message_in.role,
            content=message_in.content,
            provider=message_in.provider,
            message_metadata=message_in.message_metadata,
            created_at=now,
        )
        db.add(message)

        # Explicitly update parent session's updated_at timestamp to bubble it up
        session.updated_at = now

        db.commit()
        db.refresh(message)
        db.refresh(session)
        return message

    @staticmethod
    def list_messages(db: Session, session_id: uuid.UUID) -> List[MessageModel]:
        # Verify that parent session exists
        SessionService.get_session(db, session_id)

        stmt = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(asc(MessageModel.created_at))
        )
        return list(db.scalars(stmt).all())
