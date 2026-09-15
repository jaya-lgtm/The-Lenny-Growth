# Architecture & System Design
## The Lenny Growth Assistant

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

## 2. Ingestion & Vector Retrieval Sequence Flow

```
Lenny's Transcripts             Ingestion Pipeline              PostgreSQL (pgvector)
        │                               │                                 │
        ├─ 272 Markdown files ─────────►│                                 │
        │  (Frontmatter + Transcript)   ├─ Parse metadata & guest info    │
        │                               ├─ Chunk (Recursive 500-token)    │
        │                               ├─ Embed via 768-dim Embedder ───►│ (Store documents & chunks)
        │                               │                                 ├─ Build HNSW Cosine Index
        │                               │                                 │
Query Flow:                             │                                 │
User Query ────► FastAPI Backend ───────┤                                 │
                │                       │                                 │
                ├─ 1. QueryTopicClassifier                                │
                │     • Classify domain intent (e.g. activation_onboarding)│
                │     • Strip stopword dilution & build concept queries   │
                │     • Assign negative penalties (mentorship, AI models) │
                │                       │                                 │
                ├─ 2. Dual-Path Retrieval                                 │
                │     ├─ Dense Vector Search ────────────────────────────►│ (HNSW Cosine distance <=>)
                │     └─ Lexical Hybrid Candidate Scan (ILIKE) ──────────►│ (Match primary concept terms)
                │                                                         │
                ├─ 3. TopicAwareReranker                                  │
                │     • S_comp = 0.35*S_vec + 0.30*S_lex + 0.25*S_con     │
                │                + 0.10*S_meta - P_neg                    │
                │     • Penalize off-topic tangents (-0.50)               │
                │     • Filter below min_composite_relevance (0.35)       │
                │                       │                                 │
                ├─ 4. CitationValidator                                   │
                │     • Enforce domain concept presence in cited chunks   │
                │     • Zero-padding guarantee (1 source -> 1 citation)   │
                │                       │                                 │
                ├─ 5. Grounded Agent Context Assembly                     │
                ├─ 6. Invoke Pi Coding Agent Runner ──────────────────────┤
                ▼                                                         ▼
```

---

## 3. Deployment Topology & Docker Architecture

The application runs via a multi-container Docker Compose network with host bridging:

```
                          Evaluator Browser
                                  │
          ┌───────────────────────┴───────────────────────┐
          │ http://localhost:5173                         │ http://localhost:8000
          ▼                                               ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│     lenny_growth_frontend     │               │     lenny_growth_backend      │
│     (Node 20 / Vite Server)   │               │     (Python 3.11 / FastAPI)   │
│     Container Port: 5173      │               │     Container Port: 8000      │
└──────────────┬────────────────┘               └───────────────┬───────────────┘
               │                                                │
               │ Docker Network: lenny_default                  │
               └────────────────────────────────────────────────┤
                                                                │
                                ┌───────────────────────────────┼───────────────────────────────┐
                                │                               │                               │
                                ▼                               ▼                               ▼
                ┌───────────────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────────────┐
                │        lenny_growth_db        │  │  Host Machine Gateway   │  │   Cloud LLM Providers         │
                │    (PostgreSQL 16 pgvector)   │  │ (host.docker.internal)  │  │   (OpenAI / Anthropic APIs)   │
                │      Container Port: 5432     │  │   Port: 11434 (Ollama)  │  │   HTTPS Port: 443             │
                └───────────────────────────────┘  └─────────────────────────┘  └───────────────────────────────┘
```

### Port Mappings & Network Isolation
* `5173:5173` — Frontend React UI.
* `8000:8000` — Backend FastAPI server with OpenAPI Swagger at `/docs`.
* `5432:5432` — PostgreSQL 16 database with `pgvector` extension.
* `host.docker.internal:11434` — Secure Docker-to-host bridge enabling containerized backend to communicate with host Ollama instance.

---

## 4. Data Model & Foreign Key Constraints

### 4.1 `sessions` Table
* `id` (UUID PK): Unique session identifier.
* `title` (VARCHAR 255): Conversation title.
* `user_metadata` (JSONB): Optional client metadata.
* `created_at`, `updated_at` (TIMESTAMPTZ): Timestamps.

### 4.2 `messages` Table
* `id` (UUID PK): Message identifier.
* `session_id` (UUID FK `sessions.id` ON DELETE CASCADE): Parent conversation.
* `role` (VARCHAR 20): `'user'`, `'assistant'`, `'system'`.
* `content` (TEXT): Message body.
* `provider` (VARCHAR 50): Active provider name.
* `message_metadata` (JSONB): Model name, retrieval count, source citations list, `artifact_id`, and `agent_framework: "pi-coding-agent"`.
* `created_at` (TIMESTAMPTZ): Timestamp.

### 4.3 `documents` Table
* `id` (UUID PK): Document identifier.
* `source_type` (VARCHAR 50): `'podcast'` or `'newsletter'`.
* `external_id` (VARCHAR 255): Unique external ID.
* `title` (VARCHAR 500): Episode title.
* `source_url` (VARCHAR 1000): YouTube video URL.
* `content_hash` (VARCHAR 64): SHA-256 deduplication hash.
* `doc_metadata` (JSONB): Guest name, publication date, video ID, relative path.

### 4.4 `document_chunks` Table
* `id` (UUID PK): Chunk identifier.
* `document_id` (UUID FK `documents.id` ON DELETE CASCADE): Parent document.
* `chunk_index` (INTEGER): Index in document.
* `content` (TEXT): Chunk text excerpt.
* `token_count` (INTEGER): Token length.
* `embedding` (VECTOR 768): Vector embedding with HNSW index.
* `chunk_metadata` (JSONB): Guest, title, relative path.

### 4.5 `artifacts` Table
* `id` (UUID PK): Unique immutable artifact identifier.
* `session_id` (UUID FK `sessions.id` ON DELETE CASCADE): Parent conversation.
* `message_id` (UUID FK `messages.id` ON DELETE SET NULL): Generating assistant message.
* `artifact_type` (VARCHAR 50): `'growth_action_plan'`, `'ship30_essay'`, `'framework'`, `'checklist'`, `'experiment_plan'`, `'strategy_doc'`, `'html_css'`.
* `content_format` (VARCHAR 20): `'markdown'`, `'html'`, `'text'`, `'json'`.
* `schema_version` (VARCHAR 20): `'v1.0'`.
* `title` (VARCHAR 255): Artifact title.
* `content` (TEXT): Complete artifact content.
* `metadata` (JSONB): Word counts, author, citations, tags.
* `created_at` (TIMESTAMPTZ): Timestamp.

---

## 5. Security & Sandbox Policy

### 5.1 React DOM Injection Prevention
Generated HTML is never injected into the host DOM using React's `dangerouslySetInnerHTML`.

### 5.2 Strict Iframe Isolation
HTML/CSS components render strictly inside:
```html
<iframe
  sandbox="allow-scripts"
  srcDoc={artifact.content}
  title="Rendered Artifact Sandbox"
  className="w-full h-full border-0"
/>
```
* `allow-scripts`: Permits self-contained interactive UI components (calculators, tabs, animations).
* **Omission of `allow-same-origin`**: Treats the frame as an opaque origin, strictly preventing access to host cookies, `localStorage`, `sessionStorage`, or parent window objects (`window.parent`, `window.top`).

### 5.3 Server-Side Sanitization
The `sanitize_html_content` function strips:
* External script sources (`<script src="...">`).
* Window navigation attempts (`window.top.location`, `window.parent.document`).
* Meta refresh tags (`<meta http-equiv="refresh">`).
* Base tags (`<base href="...">`).
* External form action hijacking (`<form action="http...">`).

### 5.4 Cross-Session Access Control
Artifact retrieval (`GET /api/artifacts/{id}`) and deletion support session scoping:
* Passing `?session_id=<uuid>` verifies ownership. If the artifact belongs to another session, the API returns HTTP 403 `CROSS_SESSION_ACCESS_DENIED`.

---

## 6. Observability & Structured Logging

The backend implements structured logging with contextual diagnostic tags across every layer:

```json
{
  "timestamp": "2026-09-15T12:00:00.123Z",
  "level": "INFO",
  "logger": "backend.agents.orchestrator",
  "session_id": "0cd554f3-de0f-4ddb-aa85-834f6fc97ae2",
  "mode": "ship30_essay",
  "provider": "ollama",
  "model": "llama3.2:3b",
  "retrieval_chunks_matched": 3,
  "top_score": 0.884,
  "artifact_generated_type": "ship30_essay",
  "artifact_word_count": 1248,
  "latency_ms": 1420
}
```

* **Health Probes**: `/api/health` validates database connectivity (`ok` or `degraded`).
* **Config Probes**: `/api/config` validates reachable LLM providers and models.

---

## 7. Resilience & Error Handling Matrix

| Failure Condition | Detection Mechanism | System Behavior & Response |
| :--- | :--- | :--- |
| **Ollama Daemon Offline** | Connection refused to `http://host.docker.internal:11434` | Explicit **HTTP 503** with remediation: `"Ensure Ollama is running ('ollama serve') and model is pulled"`. Zero silent fallback. |
| **Missing Cloud API Key** | Empty `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` | Explicit **HTTP 503** with message: `"OPENAI_API_KEY is not configured"`. |
| **Model Generation Timeout** | Request exceeds `LLM_TIMEOUT_SECONDS` (180s) | HTTP 504 Gateway Timeout returned with retry guidelines. |
| **Empty Retrieval Results** | Composite relevance $< 0.35$ or zero verified domain concept hits | Agent adheres to limitation policy: explicitly acknowledges lack of transcript evidence. |
| **Database Connection Failure** | SQLAlchemy DB connection pool disconnect | `/api/health` returns `degraded`. API returns HTTP 503 Service Unavailable. |
| **Cross-Session Tampering** | Query parameter `session_id` mismatch on artifact | Explicit **HTTP 403** `CROSS_SESSION_ACCESS_DENIED`. |
