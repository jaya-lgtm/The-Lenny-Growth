from typing import List, Optional, Dict, Any
import uuid
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    title: str
    source_type: str = "podcast"
    source_url: Optional[str] = None
    guest: Optional[str] = None
    relative_path: Optional[str] = None
    publish_date: Optional[str] = None
    chunk_index: int = 0
    excerpt: str
    similarity: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentContext(BaseModel):
    session_id: uuid.UUID
    user_question: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    retrieved_chunks: List[Any] = Field(default_factory=list)
    provider_override: Optional[str] = None


class AgentOutput(BaseModel):
    content: str
    provider: str
    model: str
    retrieval_count: int
    sources: List[SourceCitation]
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
