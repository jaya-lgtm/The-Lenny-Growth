import uuid
import pytest
from starlette import status
from app.retrieval.retriever import VectorRetriever
from app.retrieval.topic_classifier import QueryTopicClassifier
from app.retrieval.reranker import TopicAwareReranker
from app.retrieval.citation_validator import CitationValidator
from app.retrieval.schemas import RetrievalResult
from app.models.chunk import DocumentChunkModel
from app.models.document import DocumentModel
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate
from ingestion.embedder import DeterministicLocalEmbedder


@pytest.fixture
def retriever():
    embedder = DeterministicLocalEmbedder(dim=768)
    return VectorRetriever(embedder=embedder)


@pytest.fixture
def seed_topic_corpus(db_session):
    """
    Seeds representative multi-topic transcript corpus into the test database:
    1. An activation/onboarding episode
    2. An off-topic leadership coaching episode
    3. A PMF/retention curve episode
    4. An off-topic AI code editor episode
    5. An active chat session
    """
    embedder = DeterministicLocalEmbedder(dim=768)

    # 1. Active Chat Session
    session = SessionService.create_session(
        db=db_session, session_in=SessionCreate(title="Topic Retrieval Test Session")
    )

    # 2. Activation Document & Chunks
    doc_activation = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Mastering Onboarding and User Activation | Lauryn Isford",
        source_url="https://youtube.com/watch?v=activation-test",
        content_hash="hash-topic-activation-1",
        doc_metadata={"guest": "Lauryn Isford", "keywords": ["activation", "onboarding", "retention"]},
    )
    db_session.add(doc_activation)
    db_session.flush()

    chunk_activation_1 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_activation.id,
        chunk_index=0,
        content="Activation is the milestone where users experience the aha moment. Optimizing onboarding to eliminate friction drives long-term user retention.",
        token_count=20,
        embedding=embedder.embed_text("activation onboarding aha moment friction drives long-term user retention"),
        chunk_metadata={"guest": "Lauryn Isford"},
    )
    chunk_activation_2 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_activation.id,
        chunk_index=1,
        content="We define the setup moment, aha moment, and habit moment. Early onboarding drop-offs hurt compounding growth.",
        token_count=18,
        embedding=embedder.embed_text("setup moment aha moment habit moment onboarding drop-offs compounding growth"),
        chunk_metadata={"guest": "Lauryn Isford"},
    )
    db_session.add_all([chunk_activation_1, chunk_activation_2])

    # 3. Off-Topic Leadership Document & Chunk
    doc_leadership = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Executive Product Leadership and Coaching | Ken Norton",
        source_url="https://youtube.com/watch?v=leadership-test",
        content_hash="hash-topic-leadership-1",
        doc_metadata={"guest": "Ken Norton", "keywords": ["leadership", "management", "coaching"]},
    )
    db_session.add(doc_leadership)
    db_session.flush()

    chunk_leadership = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_leadership.id,
        chunk_index=0,
        content="In executive coaching, we focus on 1-on-1 feedback, manager compensation, executive hiring, and board meeting prep.",
        token_count=18,
        embedding=embedder.embed_text("executive coaching 1-on-1 feedback manager compensation hiring board meeting"),
        chunk_metadata={"guest": "Ken Norton"},
    )
    db_session.add(chunk_leadership)

    # 4. PMF Document & Chunk
    doc_pmf = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Finding Product-Market Fit and Retention | Casey Winters",
        source_url="https://youtube.com/watch?v=pmf-test",
        content_hash="hash-topic-pmf-1",
        doc_metadata={"guest": "Casey Winters", "keywords": ["product-market fit", "pmf", "retention"]},
    )
    db_session.add(doc_pmf)
    db_session.flush()

    chunk_pmf = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_pmf.id,
        chunk_index=0,
        content="Product-market fit is reached when cohort retention curves flatten asymptotically. Sean Ellis 40% very disappointed test is an indicator.",
        token_count=20,
        embedding=embedder.embed_text("product-market fit retention curves flatten sean ellis 40 percent very disappointed"),
        chunk_metadata={"guest": "Casey Winters"},
    )
    db_session.add(chunk_pmf)

    # 5. Off-topic AI Code Editor Document & Chunk
    doc_ai = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Building an AI code editor used by 1m developers | Windsurf",
        source_url="https://youtube.com/watch?v=ai-test",
        content_hash="hash-topic-ai-1",
        doc_metadata={"guest": "AI Founder", "keywords": ["ai", "dev tools", "ide"]},
    )
    db_session.add(doc_ai)
    db_session.flush()

    chunk_ai = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_ai.id,
        chunk_index=0,
        content="We built an AI code editor that autocompletes code blocks in Python and TypeScript inside the IDE.",
        token_count=18,
        embedding=embedder.embed_text("ai code editor autocompletes code blocks python typescript ide"),
        chunk_metadata={"guest": "AI Founder"},
    )
    db_session.add(chunk_ai)

    db_session.commit()

    return {
        "session": session,
        "doc_activation": doc_activation,
        "doc_leadership": doc_leadership,
        "doc_pmf": doc_pmf,
        "doc_ai": doc_ai,
    }


def test_activation_query_retrieves_activation_sources(db_session, seed_topic_corpus, retriever):
    """1. Activation query retrieves activation-related sources."""
    query = "What are the most important lessons from Lenny's Podcast about improving user activation?"
    results = retriever.retrieve(db_session, query=query, top_k=4)

    assert len(results) > 0
    # Must retrieve activation/onboarding sources
    titles = [r.title for r in results]
    assert any("Activation" in t or "Onboarding" in t for t in titles)
    for res in results:
        content_lower = res.content.lower()
        title_lower = res.title.lower()
        has_relevance = any(term in content_lower or term in title_lower for term in ["activation", "onboarding", "aha", "retention"])
        assert has_relevance, f"Non-activation chunk retrieved: {res.title}"


def test_leadership_sources_excluded_from_activation(db_session, seed_topic_corpus, retriever):
    """2. Leadership/team-building sources are excluded from an activation answer when unrelated."""
    query = "What are the most important lessons from Lenny's Podcast about improving user activation?"
    results = retriever.retrieve(db_session, query=query, top_k=4)

    titles = [r.title for r in results]
    # Executive leadership coaching episode must NOT be among retrieved chunks
    assert "Executive Product Leadership and Coaching | Ken Norton" not in titles


def test_pmf_queries_do_not_cite_unrelated_ai_or_sales(db_session, seed_topic_corpus, retriever):
    """3. Product-market-fit queries prioritize PMF/retention and do not cite unrelated AI code editors."""
    query = "How do I know if I have product-market fit?"
    results = retriever.retrieve(db_session, query=query, top_k=4)

    assert len(results) > 0
    titles = [r.title for r in results]
    # Should include PMF episode
    assert any("Product-Market Fit" in t or "Casey Winters" in t for t in titles)
    # Should NOT include AI code editor
    assert not any("code editor" in t.lower() or "windsurf" in t.lower() for t in titles)


def test_unrelated_chunks_fail_citation_validation():
    """4. Unrelated chunks fail citation validation."""
    intent = QueryTopicClassifier.classify("What are the best ways to improve onboarding?")
    
    unrelated_chunk = RetrievalResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        title="Executive Compensation and Board Governance",
        source_type="podcast",
        source_url="https://example.com/board",
        chunk_index=2,
        content="In this episode we cover CEO equity refresh grants, compensation committees, and managing board expectations.",
        similarity=0.34,
        metadata={"guest": "Corporate Governance Expert"},
    )

    is_valid = CitationValidator.is_chunk_valid(unrelated_chunk, intent, min_relevance=0.28)
    assert is_valid is False

    validated = CitationValidator.filter_valid_citations(
        chunks=[unrelated_chunk],
        query="What are the best ways to improve onboarding?",
        min_relevance=0.28,
    )
    assert len(validated) == 0


def test_insufficient_evidence_does_not_fabricate_citations(client, seed_topic_corpus):
    """5. Answers with insufficient evidence do not fabricate citations."""
    session_id = str(seed_topic_corpus["session"].id)
    res = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "What is quantum electrodynamics in astrophysics?",
        },
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    msg = data["message"]
    assert msg["role"] == "assistant"
    # Must not fabricate citations
    assert msg["message_metadata"]["retrieval_count"] == 0
    assert len(msg["message_metadata"]["sources"]) == 0
    assert "could not find sufficient evidence" in msg["content"].lower()


def test_single_relevant_source_accepted_without_forcing_additional_sources():
    """6. A single relevant source is accepted without forcing additional sources or padding."""
    query = "What are the most important lessons from Lenny's Podcast about improving user activation?"
    
    single_valid_chunk = RetrievalResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        title="Mastering onboarding and user activation",
        source_type="podcast",
        source_url="https://example.com/activation",
        chunk_index=1,
        content="Onboarding is the highest leverage area for activation and long-term user retention.",
        similarity=0.62,
        metadata={"guest": "Growth Lead", "composite_relevance": 0.62},
    )

    validated = CitationValidator.filter_valid_citations(
        chunks=[single_valid_chunk],
        query=query,
        min_relevance=0.28,
    )
    assert len(validated) == 1
    assert validated[0].title == "Mastering onboarding and user activation"


def test_transcript_claims_and_general_recommendations_separated(client, seed_topic_corpus):
    """7. Transcript-supported claims and general recommendations are clearly separated."""
    session_id = str(seed_topic_corpus["session"].id)
    res = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "What are the most important lessons from Lenny's Podcast about improving user activation?",
            "provider": "mock",
        },
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    content = data["message"]["content"]

    # Structure checks
    assert "### Most Important Lessons" in content
    assert "### Evidence Limitations" in content
    assert ("Lesson 1" in content or "1." in content)
    assert "Why it matters" in content
    assert "Practical implication" in content
    assert "Citation" in content
    # Ensure off-topic leadership episode is not cited
    assert "Executive Product Leadership" not in content
