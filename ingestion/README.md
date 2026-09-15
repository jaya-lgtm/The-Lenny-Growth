# Transcript & Newsletter Ingestion Pipeline

The ingestion pipeline transforms raw Lenny Podcast transcripts and Newsletter articles into normalized, overlapping text chunks with vector embeddings stored in PostgreSQL via `pgvector`.

---

## Architecture Overview

```
data/transcripts/
   ├── *.md (YAML frontmatter + body)
   ├── *.txt (Structured key-value headers + body)
   └── *.json (title, source_url, content, metadata)
       │
       ▼
   loaders.py ──> Normalizes whitespace, preserves paragraph boundaries (\n\n), extracts metadata
       │
       ▼
   chunker.py ──> Paragraph/sentence-aware overlapping chunker (default: 800 chars, 150 overlap)
       │
       ▼
   embedder.py ──> Ollama nomic-embed-text (768-dim) / OpenAI / Deterministic Local fallback
       │
       ▼
   pipeline.py ──> Deduplicates via SHA-256 content_hash & external_id, batch inserts into PostgreSQL
```

---

## Running Ingestion

Run the ingestion pipeline directly from the repository root:

```bash
# Using default config (data/transcripts, configured embedding provider)
python -m ingestion.pipeline

# Specifying custom directory or provider
python -m ingestion.pipeline --data-dir data/transcripts --provider local

# Force re-ingesting existing documents
python -m ingestion.pipeline --force
```

Or trigger ingestion via the REST API:

```bash
curl -X POST http://localhost:8000/api/ingest
```

---

## Configuration

Set the following environment variables in `.env` or system environment:

| Variable | Description | Default |
|---|---|---|
| `DATA_DIR` | Directory containing source transcripts | `data/transcripts` |
| `EMBEDDING_PROVIDER` | Embedding provider (`ollama`, `openai`, `local`) | `ollama` |
| `OLLAMA_BASE_URL` | Ollama service endpoint | `http://localhost:11434` |
| `OLLAMA_EMBEDDING_MODEL` | Embedding model name | `nomic-embed-text` |
| `EMBEDDING_DIM` | Embedding vector dimensions | `768` |
| `CHUNK_SIZE` | Max character length per chunk | `800` |
| `CHUNK_OVERLAP` | Overlapping character length | `150` |

---

## Deduplication & Idempotency

- **Document Deduplication**: Before inserting, the pipeline calculates the SHA-256 hash of the normalized content. If a document with the matching `content_hash` or `external_id` already exists, it is safely skipped.
- **Chunk Integrity**: All chunks maintain a strict `ondelete="CASCADE"` foreign key link to their parent document. Re-ingesting a document (`--force`) cleanly drops old chunks and rebuilds embeddings.
- **Demo Disclaimers**: Sample or synthetic transcripts are clearly tagged with disclaimer metadata and headers, ensuring no fabricated content is represented as official transcript material.
