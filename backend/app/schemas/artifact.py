import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class ArtifactBase(BaseModel):
    artifact_type: str = Field(..., description="Type of artifact: growth_action_plan, ship30_essay, framework, checklist, experiment_plan, strategy_doc, html_css")
    content_format: str = Field(default="markdown", description="Format of artifact content: markdown, html, json")
    schema_version: str = Field(default="v1.0", description="Schema version of artifact structure")
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    artifact_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ArtifactCreate(ArtifactBase):
    session_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None


class ArtifactResponse(ArtifactBase):
    id: uuid.UUID
    session_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtifactListResponse(BaseModel):
    items: List[ArtifactResponse]
    total: int
