import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_ROLES = {"user", "assistant", "system"}


class MessageCreate(BaseModel):
    role: str
    content: str
    provider: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        role_lower = v.strip().lower()
        if role_lower not in ALLOWED_ROLES:
            raise ValueError(
                f"Invalid role '{v}'. Allowed roles are: {', '.join(sorted(ALLOWED_ROLES))}."
            )
        return role_lower

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty.")
        return stripped


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    provider: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
