import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message_service import MessageService

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    session_id: uuid.UUID,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
):
    """Create a new message in the specified session and bump the session's updated_at."""
    return MessageService.create_message(db, session_id, message_in)


@router.get("", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
def list_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """List all messages for the specified session in chronological order."""
    return MessageService.list_messages(db, session_id)
