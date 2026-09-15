import uuid
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.message import MessageResponse
from app.schemas.artifact import ArtifactResponse
from app.agents.schemas import SourceCitation

VALID_MODES = {
    "auto",
    "grounded_qa",
    "growth_action_plan",
    "ship30_essay",
    "framework",
    "checklist",
    "experiment_plan",
    "strategy_doc",
    "html_css",
    "html_css_component",
}



class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str
    provider: Optional[str] = None
    mode: Optional[str] = "auto"
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = None

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Chat message content cannot be empty.")
        return stripped

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: Optional[str]) -> str:
        if v is None:
            return "auto"
        lowered = v.strip().lower()
        if lowered not in VALID_MODES:
            valid_list = ", ".join(sorted(VALID_MODES))
            raise ValueError(f"Invalid mode '{v}'. Must be one of: {valid_list}")
        return lowered


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    message: MessageResponse
    sources: Optional[List[SourceCitation]] = None
    provider: Optional[str] = None
    artifact: Optional[ArtifactResponse] = None

    model_config = ConfigDict(from_attributes=True)
