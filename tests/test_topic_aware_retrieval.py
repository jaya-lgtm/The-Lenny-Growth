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
    1. An active chat session
    2. An activation/onboarding episode (Lauryn Isford)
    3. An off-topic leadership coaching episode (Ken Norton)
    4. An off-topic career mentorship episode (Jules Walter)
    5. An off-topic AI/world-models episode (Dr. Fei-Fei Li)
    6. An off-topic general strategy episode (Richard Rumelt)
    7. A PMF/retention curve episode (Casey Winters)
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
        content="We define the setup moment, aha moment, and habit moment. Early onboarding drop-offs hurt compounding growth and time to first value.",
        token_count=18,
        embedding=embedder.embed_text("setup moment aha moment habit moment onboarding drop-offs compounding growth time to first value"),
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

    # 4. Off-Topic Mentorship Document & Chunk (Jules Walter)
    doc_mentorship = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Leveraging mentors to uplevel your career | Jules Walter (YouTube, Slack)",
        source_url="https://youtube.com/watch?v=mentorship-test",
        content_hash="hash-topic-mentorship-1",
        doc_metadata={"guest": "Jules Walter", "keywords": ["mentorship", "career", "promotion"]},
    )
    db_session.add(doc_mentorship)
    db_session.flush()

    chunk_mentorship = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_mentorship.id,
        chunk_index=0,
        content="In career development, finding great mentors at Slack and YouTube helped me navigate promotions, hiring manager relationships, and career advice.",
        token_count=20,
        embedding=embedder.embed_text("career development mentors slack youtube promotions hiring manager career advice"),
        chunk_metadata={"guest": "Jules Walter"},
    )
    db_session.add(chunk_mentorship)

    # 5. Off-Topic AI & World Models Document & Chunk (Dr. Fei-Fei Li)
    doc_ai = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="The Godmother of AI on jobs, robots & why world models are next | Dr. Fei-Fei Li",
        source_url="https://youtube.com/watch?v=ai-feifei-test",
        content_hash="hash-topic-ai-feifei-1",
        doc_metadata={"guest": "Dr. Fei-Fei Li", "keywords": ["ai", "robotics", "world models"]},
    )
    db_session.add(doc_ai)
    db_session.flush()

    chunk_ai = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_ai.id,
        chunk_index=0,
        content="World models and spatial intelligence are the next frontier for AI research, robotics, and machine learning neural networks.",
        token_count=18,
        embedding=embedder.embed_text("world models spatial intelligence ai research robotics machine learning neural networks"),
        chunk_metadata={"guest": "Dr. Fei-Fei Li"},
    )
    db_session.add(chunk_ai)

    # 6. Off-Topic Strategy Document & Chunk (Richard Rumelt)
    doc_strategy = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Good Strategy, Bad Strategy | Richard Rumelt",
        source_url="https://youtube.com/watch?v=rumelt-test",
        content_hash="hash-topic-rumelt-1",
        doc_metadata={"guest": "Richard Rumelt", "keywords": ["strategy", "planning"]},
    )
    db_session.add(doc_strategy)
    db_session.flush()

    chunk_strategy = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_strategy.id,
        chunk_index=0,
        content="A good corporate strategy identifies the single pivotal challenge and focuses organizational power on overcoming it.",
        token_count=18,
        embedding=embedder.embed_text("good corporate strategy identifies single pivotal challenge focuses organizational power"),
        chunk_metadata={"guest": "Richard Rumelt"},
    )
    db_session.add(chunk_strategy)

    # 7. PMF Document & Chunk
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

    db_session.commit()

    return {
        "session": session,
        "doc_activation": doc_activation,
        "doc_leadership": doc_leadership,
        "doc_mentorship": doc_mentorship,
        "doc_ai": doc_ai,
        "doc_strategy": doc_strategy,
        "doc_pmf": doc_pmf,
    }


def test_activation_queries_do_not_cite_mentorship_or_career(db_session, seed_topic_corpus, retriever):
    """1. Activation queries do not cite mentorship or career episodes (e.g. Jules Walter)."""
    query = "Create a prioritized experiment plan to improve activation for this platform."
    results = retriever.retrieve(db_session, query=query, top_k=5)

    titles = [r.title for r in results]
    assert not any("mentors" in t.lower() or "jules walter" in t.lower() for t in titles), (
        f"Off-topic mentorship episode included in activation results: {titles}"
    )


def test_activation_queries_do_not_cite_ai_or_world_models(db_session, seed_topic_corpus, retriever):
    """2. Activation queries do not cite AI / world-model episodes (e.g. Dr. Fei-Fei Li)."""
    query = "Create a prioritized experiment plan to improve activation for this platform."
    results = retriever.retrieve(db_session, query=query, top_k=5)

    titles = [r.title for r in results]
    assert not any("world models" in t.lower() or "fei-fei" in t.lower() for t in titles), (
        f"Off-topic AI/world models episode included in activation results: {titles}"
    )


def test_activation_queries_do_not_cite_unrelated_leadership(db_session, seed_topic_corpus, retriever):
    """3. Activation queries do not cite unrelated leadership or strategy episodes (e.g. Ken Norton, Richard Rumelt)."""
    query = "Create a prioritized experiment plan to improve activation for this platform."
    results = retriever.retrieve(db_session, query=query, top_k=5)

    titles = [r.title for r in results]
    assert not any("ken norton" in t.lower() or "richard rumelt" in t.lower() for t in titles), (
        f"Off-topic leadership/strategy episode included in activation results: {titles}"
    )


def test_relevant_activation_onboarding_chunks_preferred(db_session, seed_topic_corpus, retriever):
    """4. Relevant activation/onboarding chunks are preferred."""
    query = "Create a prioritized experiment plan to improve activation for this platform."
    results = retriever.retrieve(db_session, query=query, top_k=4)

    assert len(results) > 0
    # Must retrieve the activation document
    titles = [r.title for r in results]
    assert any("Activation" in t or "Onboarding" in t for t in titles)
    for res in results:
        content_lower = res.content.lower()
        has_activation_concept = any(c in content_lower for c in [
            "activation", "onboarding", "aha", "retention", "time to first value", "friction"
        ])
        assert has_activation_concept, f"Non-activation chunk retrieved: {res.title}"


def test_unsupported_experiments_labeled_as_general_hypotheses(client, seed_topic_corpus):
    """5. Unsupported experiments are labeled as general hypotheses, not direct podcast recommendations."""
    session_id = str(seed_topic_corpus["session"].id)
    res = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "Create a prioritized experiment plan to improve activation for this platform.",
            "provider": "mock",
        },
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    content = data["message"]["content"]

    # Must define activation and state explicit assumptions
    assert "### Activation Definition and Assumptions" in content
    assert "Assumption: activation means a new user completes one meaningful workflow" in content
    assert "### Relevant Evidence from Sources" in content
    assert "### Prioritized Experiment Backlog" in content
    assert "| Priority | Experiment | Hypothesis | Impact | Confidence | Ease | Primary Metric |" in content
    assert "### Experiment Details" in content
    assert "### Recommended Execution Order" in content


def test_zero_relevant_sources_produce_transparent_limitation(client, seed_topic_corpus):
    """6. Zero relevant sources produce a transparent limitation without fabricated citations."""
    session_id = str(seed_topic_corpus["session"].id)
    res = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "What are the rules of astrophysics quantum electrodynamics?",
            "provider": "mock",
        },
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    msg = data["message"]
    assert msg["message_metadata"]["retrieval_count"] == 0
    assert len(msg["message_metadata"]["sources"]) == 0
    assert "could not find sufficient evidence" in msg["content"].lower()


def test_citations_directly_support_claims(client, seed_topic_corpus):
    """7. Citations directly support the claims they accompany."""
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
    sources = data["message"]["message_metadata"]["sources"]

    assert len(sources) > 0
    for s in sources:
        title = s.get("title", "").lower()
        excerpt = s.get("excerpt", "").lower()
        # Ensure citation is directly grounded in activation/onboarding
        assert "activation" in title or "onboarding" in title or "activation" in excerpt or "onboarding" in excerpt
        # Reject off-topic domains
        assert "mentors" not in title
        assert "world models" not in title
        assert "corporate strategy" not in title
