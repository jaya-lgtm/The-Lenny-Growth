from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel, Field


class RetrievalQuery(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_type_filter: Optional[str] = None


class RetrievalResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    source_type: str
    source_url: Optional[str] = None
    chunk_index: int
    content: str
    similarity: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    query: str
    total_found: int
    results: List[RetrievalResult]
