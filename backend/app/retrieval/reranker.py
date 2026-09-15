import re
import logging
from typing import List, Dict, Any, Optional
from app.retrieval.schemas import RetrievalResult
from app.retrieval.topic_classifier import TopicIntent, QueryTopicClassifier

logger = logging.getLogger("backend.retrieval.reranker")


class TopicAwareReranker:
    """
    Reranks candidate retrieval results using a multi-signal composite score:
    - Vector semantic similarity
    - Substantive lexical query overlap
    - Domain concept density in chunk content
    - Title & metadata topic alignment
    - Negative off-topic domain penalty
    """

    def __init__(
        self,
        weight_vector: float = 0.35,
        weight_lexical: float = 0.30,
        weight_concept: float = 0.25,
        weight_metadata: float = 0.10,
        min_relevance_threshold: float = 0.28,
    ):
        self.weight_vector = weight_vector
        self.weight_lexical = weight_lexical
        self.weight_concept = weight_concept
        self.weight_metadata = weight_metadata
        self.min_relevance_threshold = min_relevance_threshold

    def compute_score(
        self,
        result: RetrievalResult,
        intent: TopicIntent,
    ) -> float:
        content_lower = result.content.lower()
        title_lower = (result.title or "").lower()
        meta_keywords = [k.lower() for k in result.metadata.get("keywords", []) if isinstance(k, str)]

        # 1. Semantic / Vector score (0.0 to 1.0)
        s_vector = max(0.0, min(1.0, float(result.similarity)))

        # 2. Substantive Lexical Overlap (excluding stopwords)
        substantive_terms = intent.substantive_terms
        if substantive_terms:
            matched_terms = [t for t in substantive_terms if t in content_lower]
            s_lexical = len(matched_terms) / len(substantive_terms)
        else:
            s_lexical = 0.0

        # 3. Domain Concept Density
        target_concepts = intent.target_concepts
        concept_hits = 0
        if target_concepts:
            for concept in target_concepts:
                if concept in content_lower:
                    concept_hits += 1
            s_concept = min(1.0, concept_hits * 0.30)
        else:
            s_concept = s_lexical

        # 4. Title & Metadata Alignment
        s_meta = 0.0
        for concept in target_concepts:
            if concept in title_lower or any(concept in kw for kw in meta_keywords):
                s_meta += 0.4
        if any(term in title_lower for term in substantive_terms):
            s_meta += 0.3
        s_meta = min(1.0, s_meta)

        # 5. Negative-Topic Penalty
        # If chunk discusses negative off-topic domains WITHOUT discussing target concepts
        negative_penalty = 0.0
        if intent.negative_terms:
            neg_in_title = any(neg in title_lower for neg in intent.negative_terms)
            neg_in_content = any(neg in content_lower for neg in intent.negative_terms)
            
            # Substantive topic requires direct concept hits, not merely conversational filler
            has_substantive_topic = concept_hits > 0
            
            if neg_in_title:
                negative_penalty += 0.60
            elif neg_in_content and not has_substantive_topic:
                negative_penalty += 0.40

        # For activation_onboarding, strictly require at least one target activation concept hit
        if intent.domain == "activation_onboarding" and concept_hits == 0:
            negative_penalty += 0.50

        # Composite score
        composite = (
            (self.weight_vector * s_vector)
            + (self.weight_lexical * s_lexical)
            + (self.weight_concept * s_concept)
            + (self.weight_metadata * s_meta)
            - negative_penalty
        )

        return round(max(0.0, min(1.0, composite)), 4)

    def rerank(
        self,
        results: List[RetrievalResult],
        query: str,
        intent: Optional[TopicIntent] = None,
        top_k: int = 4,
        threshold: Optional[float] = None,
    ) -> List[RetrievalResult]:
        if not results:
            return []

        if intent is None:
            intent = QueryTopicClassifier.classify(query)

        min_threshold = threshold if threshold is not None else self.min_relevance_threshold

        scored_results: List[tuple[RetrievalResult, float]] = []
        for res in results:
            score = self.compute_score(res, intent)
            scored_results.append((res, score))

        # Sort by composite score descending, tie-break by original similarity
        scored_results.sort(key=lambda item: (item[1], item[0].similarity), reverse=True)

        filtered_results: List[RetrievalResult] = []
        for res, score in scored_results:
            if score >= min_threshold:
                # Update result similarity with the reranked composite score and attach score to metadata
                res.similarity = score
                res.metadata["composite_relevance"] = score
                res.metadata["topic_domain"] = intent.domain
                filtered_results.append(res)
                if len(filtered_results) >= top_k:
                    break

        return filtered_results
