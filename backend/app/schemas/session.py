import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator


class SessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    user_metadata: Optional[Dict[str, Any]] = None

    @field_validator("title", mode="before")
    @classmethod
    def set_default_title_if_empty(cls, v: Optional[str]) -> str:
        if v is None or not str(v).strip():
            return "New Conversation"
        return str(v).strip()


class SessionUpdate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Session title cannot be empty.")
        return stripped


class SessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    user_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
