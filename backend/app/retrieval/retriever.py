import logging
from pathlib import Path
import sys
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.models.chunk import DocumentChunkModel
from app.models.document import DocumentModel
from app.retrieval.schemas import RetrievalQuery, RetrievalResult, RetrievalResponse
from app.retrieval.embeddings import embed_query_text
from ingestion.embedder import BaseEmbedder

logger = logging.getLogger("backend.retrieval.retriever")


class VectorRetriever:
    """Retrieves relevant transcript chunks using pgvector cosine similarity."""

    def __init__(self, embedder: Optional[BaseEmbedder] = None):
        self.embedder = embedder

    def retrieve(
        self,
        db: Session,
        query: str,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
        source_type_filter: Optional[str] = None,
    ) -> List[RetrievalResult]:
        if not query or not query.strip():
            return []

        # Generate query vector
        try:
            if self.embedder:
                query_vector = self.embedder.embed_text(query)
            else:
                query_vector = embed_query_text(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise

        # Distance calculation in pgvector: cosine distance <=>
        # Cosine similarity = 1 - cosine distance
        distance_col = DocumentChunkModel.embedding.cosine_distance(query_vector).label("distance")

        stmt = (
            select(
                DocumentChunkModel,
                DocumentModel,
                distance_col,
            )
            .join(DocumentModel, DocumentChunkModel.document_id == DocumentModel.id)
        )

        conditions = [DocumentChunkModel.embedding.isnot(None)]
        if source_type_filter:
            conditions.append(DocumentModel.source_type == source_type_filter.lower())

        stmt = stmt.where(and_(*conditions))
        # Stable ordering: lowest distance first, tie-break by ID
        stmt = stmt.order_by(distance_col.asc(), DocumentChunkModel.id.asc())
        stmt = stmt.limit(top_k * 2 if similarity_threshold is not None else top_k)

        rows = db.execute(stmt).all()
        results: List[RetrievalResult] = []

        for chunk_model, doc_model, distance in rows:
            # Distance can be float; similarity = max(0.0, 1.0 - distance)
            sim = round(max(0.0, 1.0 - float(distance)), 4)
            if similarity_threshold is not None and sim < similarity_threshold:
                continue

            results.append(
                RetrievalResult(
                    chunk_id=chunk_model.id,
                    document_id=doc_model.id,
                    title=doc_model.title,
                    source_type=doc_model.source_type,
                    source_url=doc_model.source_url,
                    chunk_index=chunk_model.chunk_index,
                    content=chunk_model.content,
                    similarity=sim,
                    metadata=chunk_model.chunk_metadata or {},
                )
            )
            if len(results) >= top_k:
                break

        return results

    def query(self, db: Session, query_in: RetrievalQuery) -> RetrievalResponse:
        results = self.retrieve(
            db=db,
            query=query_in.query,
            top_k=query_in.top_k,
            similarity_threshold=query_in.similarity_threshold,
            source_type_filter=query_in.source_type_filter,
        )
        return RetrievalResponse(
            query=query_in.query,
            total_found=len(results),
            results=results,
        )
