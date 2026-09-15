import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.orchestrator import AgentOrchestrator

from app.schemas.artifact import ArtifactResponse
from app.agents.schemas import SourceCitation

logger = logging.getLogger("backend.api.chat")
router = APIRouter(tags=["Chat"])
orchestrator = AgentOrchestrator()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the Grounded Q&A Assistant",
)
def chat_turn(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    Process a chat message in a session:
    1. Records user message.
    2. Routes intent to specialized skill or grounded Q&A.
    3. Retrieves relevant evidence from Lenny transcript corpus.
    4. Runs grounded reasoning using configured LLM provider.
    5. Generates and persists structured artifacts when requested.
    6. Records assistant response with source metadata and citations.
    """
    assistant_msg = orchestrator.process_chat_turn(
        db=db,
        session_id=request.session_id,
        user_message=request.message,
        provider_name=request.provider,
        mode=request.mode,
        top_k=request.top_k or 5,
        similarity_threshold=request.similarity_threshold,
    )

    meta = assistant_msg.message_metadata or {}
    raw_sources = meta.get("sources", [])
    citations = [SourceCitation.model_validate(s) for s in raw_sources]
    artifact_resp = (
        ArtifactResponse.model_validate(assistant_msg.artifact)
        if getattr(assistant_msg, "artifact", None)
        else None
    )

    return ChatResponse(
        session_id=request.session_id,
        message=assistant_msg,
        sources=citations,
        provider=assistant_msg.provider,
        artifact=artifact_resp,
    )
