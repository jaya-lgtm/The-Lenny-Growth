import uuid
from typing import List
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_in: SessionCreate = SessionCreate(),
    db: Session = Depends(get_db),
):
    """Create a new chat session."""
    return SessionService.create_session(db, session_in)


@router.get("", response_model=List[SessionResponse], status_code=status.HTTP_200_OK)
def list_sessions(db: Session = Depends(get_db)):
    """List all sessions ordered by updated_at descending."""
    return SessionService.list_sessions(db)


@router.get("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get details for a specific session."""
    return SessionService.get_session(db, session_id)


@router.patch("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
def update_session(
    session_id: uuid.UUID,
    session_in: SessionUpdate,
    db: Session = Depends(get_db),
):
    """Update a session title."""
    return SessionService.update_session(db, session_id, session_in)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a session and cascade delete all its messages."""
    SessionService.delete_session(db, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
