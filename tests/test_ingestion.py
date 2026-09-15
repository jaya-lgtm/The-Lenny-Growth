from pathlib import Path
import tempfile
import pytest
from ingestion.loaders import normalize_whitespace, compute_content_hash, load_markdown, load_txt, load_json
from ingestion.chunker import DocumentChunker
from ingestion.config import IngestionConfig
from ingestion.embedder import DeterministicLocalEmbedder
from ingestion.pipeline import IngestionPipeline


def test_whitespace_normalization():
    raw = "  Hello   world!\r\n\r\n\r\n\r\nThis is paragraph  two with   spaces.  \r\n"
    normalized = normalize_whitespace(raw)
    assert normalized == "Hello world!\n\nThis is paragraph two with spaces."


def test_content_hashing():
    text1 = "Identical content"
    text2 = "Identical content"
    text3 = "Different content"
    assert compute_content_hash(text1) == compute_content_hash(text2)
    assert compute_content_hash(text1) != compute_content_hash(text3)


def test_markdown_loader_with_frontmatter():
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
        f.write(
            "---\n"
            "title: \"Custom Episode\"\n"
            "source_type: \"podcast\"\n"
            "source_url: \"https://example.com/custom\"\n"
            "external_id: \"ext-001\"\n"
            "---\n\n"
            "# Custom Episode\n\n"
            "This is the body of the episode.\n"
        )
        temp_path = Path(f.name)

    try:
        doc = load_markdown(temp_path)
        assert doc.title == "Custom Episode"
        assert doc.source_type == "podcast"
        assert doc.source_url == "https://example.com/custom"
        assert doc.external_id == "ext-001"
        assert "This is the body" in doc.content
    finally:
        temp_path.unlink()


def test_document_chunker_overlap():
    chunker = DocumentChunker(chunk_size=200, chunk_overlap=50)
    text = (
        "Paragraph 1 discusses the fundamental definition of user retention in product management.\n\n"
        "Paragraph 2 discusses growth loops and how sustainable compounding engines function.\n\n"
        "Paragraph 3 discusses churn signals and how to monitor early warnings before cancellation."
    )
    chunks = chunker.chunk_text(text, {"title": "Test Doc"})
    assert len(chunks) >= 2
    assert all(c.token_count > 0 for c in chunks)
    assert all(c.chunk_index == idx for idx, c in enumerate(chunks))


def test_ingestion_pipeline_idempotency(db_session):
    """Pipeline skips existing documents on duplicate runs without re-embedding."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        doc_path = Path(tmp_dir) / "test_doc.md"
        doc_path.write_text(
            "---\n"
            "title: \"Idempotency Doc\"\n"
            "source_type: \"podcast\"\n"
            "external_id: \"idemp-001\"\n"
            "---\n\n"
            "Content that will be ingested twice to verify deduplication.\n",
            encoding="utf-8",
        )

        cfg = IngestionConfig(
            data_dir=Path(tmp_dir),
            embedding_provider="local",
        )
        pipeline = IngestionPipeline(
            config=cfg,
            embedder=DeterministicLocalEmbedder(dim=768),
        )

        # Run 1: Should insert 1 document
        res1 = pipeline.run(db=db_session)
        assert res1["discovered"] == 1
        assert res1["inserted"] == 1
        assert res1["skipped"] == 0

        # Run 2: Should skip 1 document
        res2 = pipeline.run(db=db_session)
        assert res2["discovered"] == 1
        assert res2["inserted"] == 0
        assert res2["skipped"] == 1
