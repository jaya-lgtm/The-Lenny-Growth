# Knowledge Base & Ingestion Architecture

The primary knowledge base corpus for **The Lenny Growth Assistant** is sourced from the official assignment repository:
[https://github.com/ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts)

This archive provides 303 episode transcripts from Lenny's Podcast formatted with rich YAML frontmatter and speaker dialogue.

---

## 1. Primary Corpus Structure

```
data/transcripts/
├── episodes/
│   ├── brian-balfour/
│   │   └── transcript.md
│   ├── casey-winters/
│   │   └── transcript.md
│   ├── elena-verna/
│   │   └── transcript.md
│   └── ... (303 guest folders)
├── index/
│   ├── README.md
│   └── {topic}.md
└── scripts/
    └── build-index.sh
```

### Transcript YAML Frontmatter Schema

Each episode `transcript.md` contains structured metadata parsed via `PyYAML`:

```yaml
---
guest: Brian Balfour
title: Why ChatGPT will be the next big growth channel (and how to capitalize on it) | Brian Balfour
youtube_url: https://www.youtube.com/watch?v=cX4cL6B-_aU
video_id: cX4cL6B-_aU
publish_date: 2025-08-17
description: 'Brian Balfour is the founder of Reforge, former VP of Growth at HubSpot...'
duration_seconds: 5352.0
duration: '1:29:12'
view_count: 38284
channel: "Lenny's Podcast"
keywords:
- growth
- retention
- metrics
- pricing
---
```

### Metadata Preserved in PostgreSQL
* `title`: Full episode title
* `guest`: Guest name stored in metadata
* `source_url`: YouTube URL (`youtube_url`)
* `external_id`: `video_id` or episode folder slug
* `published_at`: ISO timestamp from `publish_date`
* `relative_path`: Relative file path (e.g. `episodes/brian-balfour/transcript.md`)
* `doc_metadata`: Full JSONB object preserving duration, view count, channel, keywords, and description

---

## 2. Test Fixtures Policy

Synthetic demo transcripts are strictly quarantined in:
`tests/fixtures/synthetic_demo/`

These files are used solely for isolated offline automated unit tests (such as `test_ingestion.py` and `test_chat_agent.py`) and are never seeded into the primary knowledge base.

---

## 3. Ingestion Pipeline & Execution

### Automated Clone & Ingest Command
The pipeline can clone or update the required repository automatically:

```bash
# Clone and ingest using local deterministic embedder (fastest for offline testing)
python -m ingestion.pipeline --clone --provider local

# Ingest with Ollama (nomic-embed-text)
python -m ingestion.pipeline --provider ollama

# Re-ingest with force refresh (updates existing documents without breaking sessions/messages)
python -m ingestion.pipeline --force --provider local
```

### Trigger Ingestion via REST API
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"provider": "local", "clone": true}'
```

### Safe Refresh & Idempotency
- **No Destructive Reset**: Ingestion updates or skips documents without resetting the database.
- **Session & Message Preservation**: User sessions, conversation messages, and generated artifacts are completely untouched.
- **Deduplication**: Ingestion compares SHA-256 `content_hash` and `external_id`. Existing unchanged documents are skipped.
- **Clean Demo Command**: The `--clean-demo` flag selectively cleans old synthetic fixtures (`external_id LIKE '%demo%'`) without touching legitimate transcript records.

---

## 4. Text Normalization, Chunking & Storage (`pgvector`)

* **Normalization**: Standardizes newlines, removes tabs and non-breaking spaces, collapses inline whitespace while preserving paragraph breaks (`\n\n`), and computes SHA-256 hashes.
* **Chunking**: Target `800` characters with `150` characters overlap, assembled at paragraph and sentence boundaries to avoid slicing dialogue mid-word.
* **Storage**: Vector embeddings stored in table `document_chunks` using `Vector(768)` with an HNSW cosine similarity index:
  ```sql
  CREATE INDEX idx_document_chunks_embedding_hnsw 
  ON document_chunks USING hnsw (embedding vector_cosine_ops);
  ```

