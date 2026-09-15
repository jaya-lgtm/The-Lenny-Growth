import uuid
import pytest
from app.models.document import DocumentModel
from app.models.chunk import DocumentChunkModel
from app.retrieval.retriever import VectorRetriever
from ingestion.embedder import DeterministicLocalEmbedder


@pytest.fixture
def populated_knowledge_base(db_session):
    """Seed test database with two distinct documents and vector chunks."""
    embedder = DeterministicLocalEmbedder(dim=768)

    # Doc 1: User Activation
    doc1 = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Elena Verna on User Activation",
        source_url="https://example.com/activation",
        content_hash="hash-act-1",
    )
    db_session.add(doc1)
    db_session.flush()

    chunk1_1 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc1.id,
        chunk_index=0,
        content="Activation is defined as reaching the setup and aha moment in onboarding.",
        token_count=12,
        embedding=embedder.embed_text("Activation is defined as reaching the setup and aha moment in onboarding."),
    )
    chunk1_2 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc1.id,
        chunk_index=1,
        content="Benchmarking B2B activation metrics across SaaS tiers.",
        token_count=8,
        embedding=embedder.embed_text("Benchmarking B2B activation metrics across SaaS tiers."),
    )

    # Doc 2: Retention Loops
    doc2 = DocumentModel(
        id=uuid.uuid4(),
        source_type="newsletter",
        title="Brian Balfour on Retention Loops",
        source_url="https://example.com/retention",
        content_hash="hash-ret-2",
    )
    db_session.add(doc2)
    db_session.flush()

    chunk2_1 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc2.id,
        chunk_index=0,
        content="Retention curves must flatten to prove sustainable product market fit.",
        token_count=10,
        embedding=embedder.embed_text("Retention curves must flatten to prove sustainable product market fit."),
    )

    db_session.add_all([chunk1_1, chunk1_2, chunk2_1])
    db_session.commit()

    return {
        "doc1": doc1,
        "doc2": doc2,
        "chunk_activation": chunk1_1,
        "chunk_retention": chunk2_1,
        "embedder": embedder,
    }


def test_retrieval_ranking(db_session, populated_knowledge_base):
    """Vector similarity search ranks relevant chunks highest."""
    embedder = populated_knowledge_base["embedder"]
    retriever = VectorRetriever(embedder=embedder)

    results = retriever.retrieve(
        db=db_session,
        query="Tell me about user onboarding and activation aha moments",
        top_k=2,
    )
    assert len(results) > 0
    # Top chunk should be activation related
    assert results[0].document_id == populated_knowledge_base["doc1"].id
    assert "activation" in results[0].content.lower() or "aha" in results[0].content.lower()
    assert results[0].source_url == "https://example.com/activation"
    assert results[0].similarity > 0.0


def test_retrieval_similarity_threshold(db_session, populated_knowledge_base):
    """Setting a high similarity threshold filters out weak matches."""
    embedder = populated_knowledge_base["embedder"]
    retriever = VectorRetriever(embedder=embedder)

    # Threshold set very high (0.95) should return empty list
    results = retriever.retrieve(
        db=db_session,
        query="Completely unrelated topic about gardening and botany",
        top_k=5,
        similarity_threshold=0.95,
    )
    assert len(results) == 0


def test_empty_retrieval_handling(db_session):
    """Querying an empty database or blank query returns an empty list without error."""
    embedder = DeterministicLocalEmbedder(dim=768)
    retriever = VectorRetriever(embedder=embedder)

    results_blank = retriever.retrieve(db=db_session, query="")
    assert results_blank == []

    results_whitespace = retriever.retrieve(db=db_session, query="   ")
    assert results_whitespace == []


def test_retrieval_source_metadata_preservation(db_session, populated_knowledge_base):
    """Retrieved results preserve source title, type, url, and chunk index."""
    embedder = populated_knowledge_base["embedder"]
    retriever = VectorRetriever(embedder=embedder)

    results = retriever.retrieve(
        db=db_session,
        query="retention curves and market fit",
        top_k=1,
    )
    assert len(results) == 1
    top = results[0]
    assert top.title == "Brian Balfour on Retention Loops"
    assert top.source_type == "newsletter"
    assert top.source_url == "https://example.com/retention"
    assert top.chunk_index == 0
