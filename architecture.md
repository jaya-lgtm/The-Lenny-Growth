# Architecture & System Design
## The Lenny Growth Assistant

> **Note**: For the full version with detailed schemas, diagrams, and logging specifications, see [docs/architecture.md](file:///docs/architecture.md).

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            REACT + TYPESCRIPT FRONTEND                      │
│  ┌─────────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │   Sidebar Component     │  │ Composer (Mode / Skill Pill Selector)    │  │
│  │   • Conversation CRUD   │  │   • Auto Detect        • Ship 30 Essay   │  │
│  │   • Active Session Arts │  │   • Growth Action Plan • Framework       │  │
│  │   • DB Health Indicator │  │   • Audit Checklist    • HTML Component  │  │
│  └────────────┬────────────┘  └────────────────────┬─────────────────────┘  │
│               │                                    │                        │
│               ▼                                    ▼                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ ChatArea (Message stream + Collapsible Citations + ArtifactCard)      │  │
│  └─────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │ (Click "Open Artifact")                │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ ArtifactViewer (Claude-style slide-over panel)                        │  │
│  │  • Formatted View: Formatted Markdown OR Isolated Sandboxed Iframe    │  │
│  │    [sandbox="allow-scripts", STRICTLY NO allow-same-origin]           │  │
│  │  • Raw Source Tab: Markdown / HTML syntax viewer with byte count      │  │
│  │  • Evidence & Citations Tab: Real Lenny's Podcast quotes & YouTube links │  │
│  │  • Actions: Clipboard Copy ("Copied!" badge), Download, Fullscreen    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ HTTP REST API (JSON)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND & AGENT ENGINE                      │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────┐  │
│  │ REST Routing Layer    │  │ Intent Router         │  │ Pi Coding Agent │  │
│  │ • /api/chat           │  │ • Explicit Skill Mode │  │ Framework       │  │
│  │ • /api/artifacts/*    │  │ • Heuristic Keyword   │  │ • ToolRegistry  │  │
│  │ • /api/sessions/*     │  │   Classification      │  │ • RetrievalTool │  │
│  │ • /api/health,/config │  └───────────┬───────────┘  │ • Sandbox       │  │
│  └───────────┬───────────┘              │              └────────┬────────┘  │
│              │                          ▼                       │           │
│              │             ┌─────────────────────────┐          │           │
│              │             │ Grounded Generators     │          │           │
│              │             │ • Ship 30 (1,000-1,500w)│          │           │
│              │             │ • Growth Action Plans   │          │           │
│              │             │ • HTML/CSS Sanitizer    │          │           │
│              │             └────────────┬────────────┘          │           │
│              ▼                          ▼                       ▼           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Multi-Provider LLM & Embedding Abstraction Layer                      │  │
│  │ • Mock (deterministic offline default for evaluators)                 │  │
│  │ • Ollama (llama3.2:3b, nomic-embed-text via HTTP)                     │  │
│  │ • OpenAI (gpt-4o-mini REST adapter)                                   │  │
│  │ • Anthropic (claude-3-5-sonnet REST adapter)                          │  │
│  │ • Zero silent fallback (explicit HTTP 503 on provider outage)         │  │
│  └─────────────────────────────────┬─────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ SQLAlchemy 2.0 ORM & Psycopg2
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     POSTGRESQL 16 (pgvector) DATABASE                       │
│  ┌─────────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │ documents               │  │ document_chunks                          │  │
│  │ • 272 Podcast episodes  │  │ • 37,226 chunks with 768-dim embeddings │  │
│  │ • guest, title, URL,    │  │ • HNSW index (cosine similarity)         │  │
│  │   pub_date, file_path   │  │ • chunk_index, token_count, metadata     │  │
│  └────────────┬────────────┘  └────────────────────┬─────────────────────┘  │
│               │ ON DELETE CASCADE                  │                        │
│               └────────────────────────────────────┘                        │
│  ┌─────────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │ sessions                │  │ messages                                 │  │
│  │ • id (UUID PK)          │  │ • id (UUID PK), session_id (FK CASCADE)  │  │
│  │ • title, timestamps     │  │ • role, content, provider, metadata      │  │
│  └────────────┬────────────┘  └────────────────────┬─────────────────────┘  │
│               │ ON DELETE CASCADE                  │ ON DELETE SET NULL     │
│               └──────────────────┬─────────────────┘                        │
│                                  ▼                                          │
│                       ┌─────────────────────────┐                           │
│                       │ artifacts               │                           │
│                       │ • id (UUID PK)          │                           │
│                       │ • session_id (FK)       │                           │
│                       │ • message_id (FK)       │                           │
│                       │ • artifact_type         │                           │
│                       │ • content_format        │                           │
│                       │ • schema_version        │                           │
│                       │ • title, content, meta  │                           │
│                       └─────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Architecture Components

1. **FastAPI & Agent Engine**: Uses the official Pi Coding Agent framework (`pi-coding-agent`), `ToolRegistry`, and PostgreSQL pgvector HNSW index.
2. **Deterministic & Local Embedders**: Local 768-dimensional deterministic embedder ensures instant offline evaluator testing; native `nomic-embed-text` supported via Ollama.
3. **Database Schema & Migrations**: Managed via Alembic (`001_initial_schema`, `002_documents_and_chunks`, `003_artifacts`). Foreign keys ensure CASCADE deletion of messages and artifacts when a session is deleted.
4. **Security & Sandbox Isolation**: Untrusted HTML renders inside `<iframe sandbox="allow-scripts">` strictly omitting `allow-same-origin`, preventing DOM or cookie access.
5. **Zero Silent Fallback**: When Ollama or an unconfigured cloud provider is requested, the system returns an explicit HTTP 503 with helpful remediation instructions.

---

For complete flows, sequence diagrams, and failure matrices, refer to [docs/architecture.md](file:///docs/architecture.md).
