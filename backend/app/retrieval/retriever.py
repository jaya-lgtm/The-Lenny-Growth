import logging
from pathlib import Path
import sys
from typing import List, Optional, Set
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.config import get_settings
from app.models.chunk import DocumentChunkModel
from app.models.document import DocumentModel
from app.retrieval.schemas import RetrievalQuery, RetrievalResult, RetrievalResponse
from app.retrieval.embeddings import embed_query_text
from app.retrieval.topic_classifier import QueryTopicClassifier, TopicIntent
from app.retrieval.reranker import TopicAwareReranker
from app.retrieval.citation_validator import CitationValidator
from ingestion.embedder import BaseEmbedder

logger = logging.getLogger("backend.retrieval.retriever")


class VectorRetriever:
    """
    Topic-aware hybrid retriever for Lenny's Podcast and Newsletter knowledge base.
    Combines dense vector similarity with lexical term retrieval, multi-signal topic
    reranking, and citation validation to deliver highly relevant, grounded transcript evidence.
    """

    def __init__(
        self,
        embedder: Optional[BaseEmbedder] = None,
        reranker: Optional[TopicAwareReranker] = None,
    ):
        self.embedder = embedder
        self.settings = get_settings()
        self.reranker = reranker or TopicAwareReranker(
            min_relevance_threshold=self.settings.min_composite_relevance
        )

    def _generate_embedding(self, text: str) -> List[float]:
        if self.embedder:
            return self.embedder.embed_text(text)
        return embed_query_text(text)

    def retrieve(
        self,
        db: Session,
        query: str,
        top_k: int = 4,
        similarity_threshold: Optional[float] = None,
        source_type_filter: Optional[str] = None,
    ) -> List[RetrievalResult]:
        if not query or not query.strip():
            return []

        intent = QueryTopicClassifier.classify(query)
        candidate_pool_size = max(top_k * 5, self.settings.retrieval_candidate_pool)

        # 1. Embed query: use clean substantive terms to avoid stopword dilution, or full query
        embed_text = intent.clean_query if intent.clean_query else query
        try:
            query_vector = self._generate_embedding(embed_text)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise

        # 2. Vector search candidate retrieval
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
        stmt = stmt.order_by(distance_col.asc(), DocumentChunkModel.id.asc())
        stmt = stmt.limit(candidate_pool_size)

        rows = db.execute(stmt).all()

        candidates: List[RetrievalResult] = []
        seen_chunk_ids: Set[int] = set()

        for chunk_model, doc_model, distance in rows:
            sim = round(max(0.0, 1.0 - float(distance)), 4)
            candidates.append(
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
            seen_chunk_ids.add(chunk_model.id)

        # 3. Hybrid Lexical candidate retrieval (if enabled and substantive terms exist)
        if self.settings.enable_lexical_hybrid and (intent.substantive_terms or intent.target_concepts):
            primary_terms = intent.substantive_terms[:3] or intent.target_concepts[:2]
            lex_clauses = []
            for term in primary_terms:
                if len(term) >= 4:
                    lex_clauses.append(DocumentChunkModel.content.ilike(f"%{term}%"))
                    lex_clauses.append(DocumentModel.title.ilike(f"%{term}%"))

            if lex_clauses:
                lex_stmt = (
                    select(DocumentChunkModel, DocumentModel)
                    .join(DocumentModel, DocumentChunkModel.document_id == DocumentModel.id)
                    .where(and_(DocumentChunkModel.embedding.isnot(None), or_(*lex_clauses)))
                )
                if source_type_filter:
                    lex_stmt = lex_stmt.where(DocumentModel.source_type == source_type_filter.lower())

                lex_stmt = lex_stmt.limit(15)
                lex_rows = db.execute(lex_stmt).all()

                for chunk_model, doc_model in lex_rows:
                    if chunk_model.id not in seen_chunk_ids:
                        # Compute similarity with query vector
                        try:
                            dot = sum(a * b for a, b in zip(chunk_model.embedding, query_vector))
                            sim = round(max(0.0, float(dot)), 4)
                        except Exception:
                            sim = 0.20

                        candidates.append(
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
                        seen_chunk_ids.add(chunk_model.id)

        # 4. Rerank and filter candidates
        if self.settings.enable_reranking:
            effective_threshold = (
                similarity_threshold
                if similarity_threshold is not None
                else self.settings.min_composite_relevance
            )
            reranked = self.reranker.rerank(
                results=candidates,
                query=query,
                intent=intent,
                top_k=top_k,
                threshold=effective_threshold,
            )
            # Conservative citation validation
            validated = CitationValidator.filter_valid_citations(
                chunks=reranked,
                query=query,
                min_relevance=effective_threshold,
            )
            return validated[:top_k]
        else:
            # Fallback legacy behavior
            filtered = [
                r for r in candidates
                if similarity_threshold is None or r.similarity >= similarity_threshold
            ]
            return filtered[:top_k]

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
