import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from app.models.document import DocumentModel
from app.models.chunk import DocumentChunkModel
from ingestion.loaders import compute_content_hash
from ingestion.embedder import DeterministicLocalEmbedder


def test_document_creation_and_persistence(db_session):
    """Document is stored with source_type, title, content_hash, and metadata."""
    content = "Sample transcript content about retention."
    content_hash = compute_content_hash(content)

    doc = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Elena Verna on PLG",
        source_url="https://example.com/podcast-elena",
        external_id="ext-elena-001",
        content_hash=content_hash,
        doc_metadata={"guest": "Elena Verna", "topics": ["PLG", "B2B"]},
    )
    db_session.add(doc)
    db_session.commit()

    saved = db_session.get(DocumentModel, doc.id)
    assert saved is not None
    assert saved.title == "Elena Verna on PLG"
    assert saved.source_type == "podcast"
    assert saved.source_url == "https://example.com/podcast-elena"
    assert saved.content_hash == content_hash
    assert saved.doc_metadata["guest"] == "Elena Verna"
    assert saved.created_at is not None


def test_chunk_creation_with_vector_embedding(db_session):
    """Chunk is linked to document with 768-dim vector embedding and metadata."""
    embedder = DeterministicLocalEmbedder(dim=768)
    content = "Activation requires reaching the Aha! moment quickly."
    emb = embedder.embed_text(content)

    doc = DocumentModel(
        id=uuid.uuid4(),
        source_type="newsletter",
        title="Activation Benchmarks",
        content_hash=compute_content_hash(content),
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        content=content,
        token_count=8,
        embedding=emb,
        chunk_metadata={"section": "Overview"},
    )
    db_session.add(chunk)
    db_session.commit()

    saved_chunk = db_session.get(DocumentChunkModel, chunk.id)
    assert saved_chunk is not None
    assert saved_chunk.document_id == doc.id
    assert saved_chunk.chunk_index == 0
    assert saved_chunk.token_count == 8
    assert len(saved_chunk.embedding) == 768
    assert saved_chunk.chunk_metadata["section"] == "Overview"


def test_document_cascade_deletion(db_session):
    """Deleting a document cascades and deletes all child chunks."""
    doc = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Cascade Test Episode",
        content_hash="hash-cascade-1",
    )
    db_session.add(doc)
    db_session.flush()

    chunk1 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        content="Chunk 1 content",
    )
    chunk2 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=1,
        content="Chunk 2 content",
    )
    db_session.add_all([chunk1, chunk2])
    db_session.commit()

    # Verify chunks exist
    chunks = db_session.scalars(
        select(DocumentChunkModel).where(DocumentChunkModel.document_id == doc.id)
    ).all()
    assert len(chunks) == 2

    # Delete parent document
    db_session.delete(doc)
    db_session.commit()

    # Chunks must be deleted
    remaining = db_session.scalars(
        select(DocumentChunkModel).where(DocumentChunkModel.document_id == doc.id)
    ).all()
    assert len(remaining) == 0
