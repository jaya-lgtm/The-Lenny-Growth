from pathlib import Path
import pytest
from sqlalchemy import select

from app.models.document import DocumentModel
from app.models.chunk import DocumentChunkModel
from ingestion.loaders import load_markdown
from ingestion.chunker import DocumentChunker
from ingestion.embedder import DeterministicLocalEmbedder
from ingestion.config import IngestionConfig
from ingestion.pipeline import IngestionPipeline
from app.retrieval.retriever import VectorRetriever


def get_real_sample_path() -> Path:
    candidates = [
        Path("data/transcripts/episodes/brian-balfour/transcript.md"),
        Path("data/transcripts/episodes/casey-winters/transcript.md"),
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fallback to any transcript.md in data/transcripts
    any_transcript = list(Path("data/transcripts").rglob("transcript.md"))
    if any_transcript:
        return any_transcript[0]
    pytest.skip("ChatPRD transcript repository not yet present at data/transcripts")


def test_real_transcript_loaded_and_frontmatter_parsed():
    """Confirms a real episode transcript from ChatPRD loads and extracts rich YAML frontmatter."""
    sample_path = get_real_sample_path()
    doc = load_markdown(sample_path)

    assert doc.title is not None and len(doc.title) > 5
    assert doc.source_type == "podcast"
    assert doc.source_url and doc.source_url.startswith("https://")
    assert doc.external_id is not None
    assert doc.metadata.get("guest") is not None
    assert "relative_path" in doc.metadata
    assert doc.metadata["relative_path"].endswith("transcript.md")
    assert len(doc.content) > 1000


def test_real_transcript_chunking_and_metadata_preservation():
    """Confirms chunks preserve guest, title, relative file path, and external ID."""
    sample_path = get_real_sample_path()
    doc = load_markdown(sample_path)
    chunker = DocumentChunker(chunk_size=800, chunk_overlap=150)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 5
    first_chunk = chunks[0]
    assert first_chunk.metadata.get("guest") == doc.metadata.get("guest")
    assert first_chunk.metadata.get("title") == doc.title
    assert first_chunk.metadata.get("relative_path") == doc.metadata.get("relative_path")
    assert first_chunk.metadata.get("source_url") == doc.source_url


def test_real_transcript_indexing_and_vector_retrieval(db_session):
    """Confirms indexing into PostgreSQL and vector retrieval returning real source metadata."""
    sample_path = get_real_sample_path()
    embedder = DeterministicLocalEmbedder(dim=768)

    # Ingest single real transcript into isolated test db_session
    doc = load_markdown(sample_path)
    doc_record = DocumentModel(
        source_type=doc.source_type,
        title=doc.title,
        source_url=doc.source_url,
        published_at=doc.published_at,
        external_id=doc.external_id,
        content_hash=doc.content_hash,
        doc_metadata=doc.metadata,
    )
    db_session.add(doc_record)
    db_session.flush()

    chunker = DocumentChunker(chunk_size=800, chunk_overlap=150)
    chunks = chunker.chunk_document(doc)[:10]  # First 10 chunks for fast indexing
    contents = [c.content for c in chunks]
    embeddings = embedder.embed_batch(contents)

    for c, emb in zip(chunks, embeddings):
        db_session.add(
            DocumentChunkModel(
                document_id=doc_record.id,
                chunk_index=c.chunk_index,
                content=c.content,
                token_count=c.token_count,
                embedding=emb,
                chunk_metadata=c.metadata,
            )
        )
    db_session.commit()

    # Query using pgvector VectorRetriever
    retriever = VectorRetriever(embedder=embedder)
    results = retriever.retrieve(
        db=db_session,
        query="ChatGPT distribution platform growth",
        top_k=3,
    )

    assert len(results) > 0
    top = results[0]
    assert top.title == doc.title
    assert top.source_type == "podcast"
    assert top.metadata.get("guest") == doc.metadata.get("guest")
    assert top.metadata.get("relative_path") == doc.metadata.get("relative_path")


def test_chat_agent_cites_actual_transcript(client, db_session):
    """Confirms /api/chat returns citations pointing to actual ChatPRD transcript files."""
    sample_path = get_real_sample_path()
    embedder = DeterministicLocalEmbedder(dim=768)

    # Ingest document
    doc = load_markdown(sample_path)
    doc_record = DocumentModel(
        source_type=doc.source_type,
        title=doc.title,
        source_url=doc.source_url,
        published_at=doc.published_at,
        external_id=doc.external_id,
        content_hash=doc.content_hash,
        doc_metadata=doc.metadata,
    )
    db_session.add(doc_record)
    db_session.flush()

    chunker = DocumentChunker(chunk_size=800, chunk_overlap=150)
    chunks = chunker.chunk_document(doc)[:5]
    contents = [c.content for c in chunks]
    embeddings = embedder.embed_batch(contents)

    for c, emb in zip(chunks, embeddings):
        db_session.add(
            DocumentChunkModel(
                document_id=doc_record.id,
                chunk_index=c.chunk_index,
                content=c.content,
                token_count=c.token_count,
                embedding=emb,
                chunk_metadata=c.metadata,
            )
        )
    db_session.commit()

    # Create session
    s_res = client.post("/api/sessions", json={"title": "Real Corpus Smoke Test"})
    assert s_res.status_code == 201
    sid = s_res.json()["id"]

    # Chat
    chat_res = client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Why will ChatGPT be a major growth channel?",
            "provider": "mock",
        },
    )
    assert chat_res.status_code == 200
    data = chat_res.json()
    msg = data["message"]
    assert msg["role"] == "assistant"
    sources = msg["message_metadata"]["sources"]
    assert len(sources) > 0

    first_source = sources[0]
    assert first_source["title"] == doc.title
    assert first_source.get("guest") == doc.metadata.get("guest")
    assert first_source.get("relative_path") == doc.metadata.get("relative_path")
