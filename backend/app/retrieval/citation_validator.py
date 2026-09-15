import logging
from typing import List, Optional
from app.retrieval.schemas import RetrievalResult
from app.retrieval.topic_classifier import QueryTopicClassifier, TopicIntent

logger = logging.getLogger("backend.retrieval.citation_validator")


class CitationValidator:
    """
    Validates candidate retrieval chunks before citation generation and persistence.
    Ensures that citations directly support the topic of the query,
    filters out keyword-only or off-topic matches, prevents citation padding,
    and allows single-source or zero-source outcomes.
    """

    @staticmethod
    def is_chunk_valid(
        chunk: RetrievalResult,
        intent: TopicIntent,
        min_relevance: float = 0.28,
    ) -> bool:
        score = chunk.metadata.get("composite_relevance", chunk.similarity)
        if score < min_relevance:
            logger.info(f"Rejected chunk {chunk.chunk_id}: score {score} < {min_relevance}")
            return False

        content_lower = chunk.content.lower()
        title_lower = (chunk.title or "").lower()

        # Check for off-topic domain collision (e.g. leadership when asking about activation)
        if intent.negative_terms:
            has_neg_title = any(neg in title_lower for neg in intent.negative_terms)
            has_neg_content = any(neg in content_lower for neg in intent.negative_terms)
            has_positive_concept = any(concept in content_lower for concept in intent.target_concepts)
            
            if (has_neg_title or has_neg_content) and not has_positive_concept:
                logger.info(f"Rejected chunk {chunk.chunk_id} from '{chunk.title}': off-topic domain match")
                return False

        # Ensure chunk actually mentions at least one substantive query concept or target concept
        # (prevents chunks that only shared common English grammatical words from being cited)
        matches_concept = any(c in content_lower for c in intent.target_concepts)
        matches_substantive = any(t in content_lower for t in intent.substantive_terms)
        
        # If vector similarity is extraordinarily high (> 0.50), allow it even without exact keywords
        # to honor semantic relevance requirement (rule 5)
        is_high_semantic = chunk.similarity >= 0.50

        if not (matches_concept or matches_substantive or is_high_semantic):
            logger.info(f"Rejected chunk {chunk.chunk_id}: lacks concept/substantive overlap and insufficient semantic score")
            return False

        return True

    @classmethod
    def filter_valid_citations(
        cls,
        chunks: List[RetrievalResult],
        query: str,
        min_relevance: float = 0.28,
    ) -> List[RetrievalResult]:
        """
        Filters and validates candidate chunks.
        Never pads citations: returns precisely the valid subset (0, 1, 2, ...).
        """
        if not chunks:
            return []

        intent = QueryTopicClassifier.classify(query)
        valid: List[RetrievalResult] = []

        seen_docs = set()
        for chunk in chunks:
            if cls.is_chunk_valid(chunk, intent, min_relevance=min_relevance):
                # Prefer diverse documents if multiple chunks from same doc exist
                doc_key = chunk.document_id
                valid.append(chunk)
                seen_docs.add(doc_key)

        logger.info(f"Validated {len(valid)} out of {len(chunks)} candidate chunks for query '{query[:40]}'")
        return valid
