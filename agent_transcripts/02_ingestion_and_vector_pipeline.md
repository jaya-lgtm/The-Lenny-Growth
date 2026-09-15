# Coding Agent Transcript: Milestone 2 — Knowledge Base Ingestion & Vector Pipeline

## Task Objective
Clone and index transcripts from the `ChatPRD/lennys-podcast-transcripts` repository, chunk the markdown content with metadata (guest, title, YouTube URL, publication date), generate 768-dimensional embeddings, and store them in PostgreSQL with an HNSW cosine index.

---

## Attempt 1: Embedding Vector Dimension Mismatch
* **Agent Action**: Initial implementation tested with Ollama's `llama3` default embeddings (4096 dimensions) while the database schema in migration `002_documents_and_chunks.py` was defined as `Vector(768)`.
* **Issue Encountered**:
  Ingestion script failed during chunk insertion:
  ```text
  sqlalchemy.exc.DataError: (psycopg2.errors.DataException) expected 768 dimensions, not 4096
  DETAIL: column "embedding" is of type vector(768) but expression is of type vector(4096)
  ```
* **Diagnosis**:
  Ollama's generative models output 4096-dim vectors, whereas the standard embedding models (`nomic-embed-text`) produce 768-dim vectors matching the HNSW index specifications.
* **Correction & Fix**:
  1. Standardized all embedding components on 768 dimensions.
  2. Configured Ollama embedder to target `nomic-embed-text` with explicit 768-dim validation:
     ```python
     class OllamaEmbedder(BaseEmbedder):
         def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text", dim: int = 768):
             ...
     ```
  3. Built `DeterministicLocalEmbedder` (768 dimensions) using token hashing and n-gram term frequencies to guarantee offline evaluator functionality when Ollama or GPUs are absent.

---

## Attempt 2: Document Chunking Overlap & Empty Chunks
* **Agent Action**: Created regular expression-based paragraph splitter.
* **Issue Encountered**:
  Some episodes produced zero chunks or massive single chunks (>8,000 tokens) because certain transcripts in the ChatPRD repository use continuous text without double newlines, or contain irregular YouTube timestamp markers.
* **Diagnosis**:
  Splitting solely on `\n\n` caused irregular transcripts to be treated as one single block, exceeding token boundaries and degrading cosine retrieval accuracy.
* **Correction & Fix**:
  Implemented recursive chunking with token counting (`RecursiveCharacterTextSplitter` equivalent):
  - Chunk size: ~500 tokens (2,000 characters).
  - Overlap: ~50 tokens (200 characters) to preserve contextual continuity across chunk boundaries.
  - Metadata preservation: Guest, episode title, and YouTube link injected into every individual `document_chunk` record.
  - Verified with `test_ingestion.py` and `test_documents_and_chunks.py`.
