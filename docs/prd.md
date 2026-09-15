# Product Requirements Document (PRD) & Forward Deployment Brief
## The Lenny Growth Assistant

---

## 1. Forward Deployment Discovery Brief

### 1.1 User Persona & Problem Statement
* **Primary Users**: Product Managers, Startup Founders, Growth Leads, and Strategy Operators.
* **Job to be Done**: Turn strategic product and growth wisdom from over 300 Lenny's Podcast and Newsletter episodes into tactical, evidence-backed deliverables (playbooks, checklists, frameworks, experiment plans, essays, and interactive components) without having to manually read hundreds of transcripts or craft complex prompts.
* **Pain Points Removed**:
  1. **Information Fragmentation**: Thousands of hours of audio and millions of words of transcripts are scattered across episodes and difficult to search semantically.
  2. **Hallucination & Lack of Trust**: Generic LLM chats invent plausible-sounding metrics and frameworks without factual attribution.
  3. **Prompt Fatigue**: Users do not want to engineer prompts or specify formatting constraints; they want immediate, structured, executive-ready artifacts.
  4. **Context Switching**: Reviewing code or copy-pasting markdown into external tools interrupts product workflows.

### 1.2 Measurable Success Metrics
1. **Evidence Grounding Ratio**: $\ge 95\%$ of substantive claims in generated answers and artifacts trace directly to indexed ChatPRD transcript chunks with valid guest and YouTube links.
2. **Unsupported Query Safety**: $100\%$ of out-of-domain or ungrounded questions gracefully acknowledge knowledge boundaries rather than hallucinating.
3. **Artifact Isolation & Safety**: Zero iframe same-origin escapes (`allow-same-origin` is strictly omitted) and zero direct React DOM injection.
4. **Evaluator Time-to-First-Value**: An evaluator can clone the repository, run `docker compose up -d`, and generate their first grounded artifact in $< 3$ minutes.
5. **Ship 30 Compliance**: 100% of generated Ship 30 essays fall strictly within the 1,000–1,500 word target range with hook, 3 structured parts, and takeaways.

### 1.3 Strategic Assumptions
1. **Corpus Authority**: The public repository [ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts) represents the primary factual truth.
2. **Evaluator Machine Constraints**: Evaluator laptops may not have high-end GPUs or Ollama pre-installed. Therefore, the system ships with a zero-setup `mock` provider default and local 768-dim deterministic embedder, alongside native Ollama (`llama3.2:3b`, `nomic-embed-text`) and cloud options (`OpenAI`, `Anthropic`).
3. **Immutability Principle**: Generated artifacts must be immutable records of specific conversation points. Regeneration creates a new artifact version with a distinct UUID rather than overwriting historical deliverables.
4. **Single-Organization / Workgroup Context**: Focus is on team collaboration within conversational sessions. Heavy enterprise SSO and RBAC were intentionally prioritized after core agentic grounding and artifact rendering.

### 1.4 Scope Decisions (Included vs. Excluded)
* **Included**:
  * FastAPI backend with PostgreSQL 16 + pgvector persistence and Alembic migrations.
  * Pi Coding Agent framework (`pi-coding-agent`) with `ToolRegistry` and `KnowledgeRetrievalTool`.
  * 7 Specialized Growth Skills: Activation/Onboarding Plans, Retention Frameworks, PMF Checklists, Growth Loops, Experiment Plans, Strategy Documents, and Ship 30 Essays.
  * In-App Artifact Viewer (Claude-style slide-over) with Formatted Markdown, Raw Code, and Evidence/Citations tabs.
  * Secure HTML/CSS rendering inside a sandboxed `<iframe>` (`sandbox="allow-scripts"` without `allow-same-origin`).
  * Cross-session access isolation (`CROSS_SESSION_ACCESS_DENIED` 403 checks).
* **Intentionally Excluded**:
  * *Arbitrary Python Code Execution*: Permitting users to execute Python code in the container introduces container breakout risks; artifact generation focuses on Markdown and isolated HTML/CSS.
  * *Live Web Scraping*: Kept the knowledge base strictly grounded in the ChatPRD corpus to prevent untrusted web pollution.
  * *Multi-Tenant Billing*: Kept the deployment lean and focused on local and private evaluation.

### 1.5 Key Risks & Mitigation Trade-offs
| Risk | Severity | Mitigation & Architecture Trade-off |
| :--- | :---: | :--- |
| **Hallucination of Growth Metrics** | High | Vector cosine similarity threshold filtering ($0.5$ min score); prompt instructions mandate citing specific episodes or admitting absence of evidence. |
| **Evaluator Local Daemon Unavailability** | High | Explicit HTTP 503 error envelopes when Ollama is down (no silent switching), coupled with an out-of-the-box `mock` provider default. |
| **XSS / HTML DOM Hijacking** | Critical | Strict iframe sandboxing with `sandbox="allow-scripts"` without `allow-same-origin`. Generated HTML is never injected into the React DOM. Server-side regex sanitizes external scripts, meta refresh, and parent navigation. |
| **Cross-Session Data Leakage** | Medium | Foreign key constraints cascade artifacts to sessions. API endpoints enforce session scoping on artifact retrieval and deletion. |

---

## 2. Core Functional Requirements & Specifications

### 2.1 API, Sessions & Persistence
* **FastAPI**: REST endpoints for health, sessions, messages, chat, and artifacts with Pydantic v2 validation and structured error envelopes (`{ error: { code, message, details } }`).
* **Agent Integration**: Chat execution powered by Pi Coding Agent (`pi_agent.agent.Agent`, `pi_agent.tools.registry.ToolRegistry`).
* **Session Handling**: Independent conversation sessions with titles, timestamps, and message histories.
* **PostgreSQL + pgvector**: Persisted in PostgreSQL 16 with `vector` extension and Alembic versions `001`, `002`, `003`.

### 2.2 Flexible LLM Configuration
* **Configurable Providers**: `mock` (offline default), `ollama` (local demo), `openai` (cloud), `anthropic` (cloud).
* **Explicit Behavior**: No silent fallback between providers. Visible provider badges in UI.
* **Runtime Config**: `/api/config` endpoint surfaces real-time provider reachability.

### 2.3 Knowledge Base & Grounding
* **Corpus**: 272 unique episode documents, 37,226 chunks indexed in pgvector.
* **Traceability**: Every chunk stores guest, title, YouTube URL, relative file path, and excerpt.
* **Grounding Enforcement**: System prompts forbid hallucination. Out-of-domain questions acknowledge absence of transcript support.

### 2.4 Product Tasks
* **Grounded Q&A**: Strict synthesis from transcripts with collapsible source citation cards.
* **Ship 30 Content Skill**: Generates 1,000–1,500 word essays with hook, 3 parts, actionable takeaways, and source citations.
* **Artifact Viewer**: Renders Markdown and Sandboxed HTML/CSS beside the chat with copy and download actions.

---

## 3. End-to-End User & System Flows

### Flow 1: Grounded Conversational Q&A Flow
```
User                       Frontend (React)              FastAPI (/api/chat)         pgvector / DB       LLM Provider
 │                                │                               │                        │                  │
 ├─ Types question ──────────────►│                               │                        │                  │
 │                                ├─ POST /api/chat ─────────────►│                        │                  │
 │                                │  { session_id, message, mode }│                        │                  │
 │                                │                               ├─ Embed query ─────────►│                  │
 │                                │                               │◄- Vector similarity ───┤                  │
 │                                │                               │   (Top-k chunks, score)│                  │
 │                                │                               ├─ Build Prompt + Tool ─►│                  │
 │                                │                               │  (System prompt + RAG) ├─────────────────►│
 │                                │                               │                        │◄- Completion ────┤
 │                                │                               ├─ Save message & cites ─►│                 │
 │                                │◄- 200 OK (Answer + Citations)─┤                        │                  │
 │◄- Render bubble + Citations ───┤                               │                        │                  │
```

### Flow 2: Artifact Generation & Sandboxed Rendering Flow
```
User                       Frontend (React)              FastAPI (/api/chat)        Skills / Sanitizer   Artifacts DB
 │                                │                               │                        │                  │
 ├─ Selects "Ship 30 Essay" ─────►│                               │                        │                  │
 │  or "HTML Component"           ├─ POST /api/chat ─────────────►│                        │                  │
 │                                │  { mode: "ship30_essay" }     ├─ Retrieve chunks ─────►│                  │
 │                                │                               ├─ Generate Artifact ───►│                  │
 │                                │                               │◄- Raw Artifact Content ┤                  │
 │                                │                               ├─ Sanitize HTML/CSS ───►│                  │
 │                                │                               │◄- Clean Artifact ──────┤                  │
 │                                │                               ├─ Persist Artifact ───────────────────────►│
 │                                │◄- 200 OK + Artifact Meta ─────┤                                           │
 ├─ Clicks "Open in Viewer" ─────►│                               │                                           │
 │                                ├─ Render Dual-Pane Viewer      │                                           │
 │                                │  (Markdown or Sandboxed Iframe)                                           │
```

---

## 4. Testable Acceptance Criteria (Given-When-Then)

### Scenario 1: Session Creation & Context Independence
* **Given** an active session with historical messages,
* **When** the user clicks "New Chat" in the sidebar,
* **Then** a new unique `session_id` is created, the chat area resets to empty state, and previous session messages are not visible or leaked.

### Scenario 2: Grounded Q&A with Citation Validation
* **Given** a query regarding a podcast topic (e.g., "What are the three components of activation?"),
* **When** the assistant generates an answer,
* **Then** the response must include at least one citation card containing:
  1. Guest name (e.g., Casey Winters or Eric Simons),
  2. Episode title,
  3. YouTube URL with timestamp,
  4. Match score percentage $\ge 50\%$.

### Scenario 3: Out-of-Domain Query Refusal
* **Given** a question unrelated to the podcast corpus (e.g., "What is the recipe for chocolate chip cookies?"),
* **When** submitted to the assistant,
* **Then** the assistant must acknowledge that the transcript corpus does not contain this information rather than hallucinating an answer.

### Scenario 4: Ship 30 Essay Generation
* **Given** the user selects the `Ship 30 Essay` mode pill,
* **When** asking for an essay on a growth topic,
* **Then** the assistant produces an artifact whose text contains:
  1. A clear hook statement,
  2. Exactly 3 distinct core parts with markdown headings,
  3. Actionable takeaways section,
  4. Total word count strictly within 1,000–1,500 words.

### Scenario 5: Sandboxed HTML Isolation
* **Given** a generated HTML/CSS artifact containing JavaScript,
* **When** rendered in the Artifact Viewer,
* **Then** the iframe must have `sandbox="allow-scripts"` and **no** `allow-same-origin`, preventing access to `window.parent`, cookies, or host `localStorage`.

### Scenario 6: Local Provider Outage Resilience
* **Given** the provider is set to `ollama`,
* **When** the local Ollama daemon is stopped and a message is sent,
* **Then** the API must return an explicit HTTP 503 error with an actionable troubleshooting message, and must never silently switch to a cloud provider.

---

## 5. Forward Deployment Implementation & Handoff Plan

| Phase | Milestone / Deliverable | Status |
| :--- | :--- | :---: |
| **Phase 1: Persistence & Base API** | PostgreSQL 16 + pgvector container, Alembic migrations (`001`, `002`, `003`), Sessions & Messages CRUD, Health and Config endpoints. | Complete (Verified) |
| **Phase 2: Knowledge Ingestion & RAG** | ChatPRD transcript parser, chunking, 768-dim embeddings, vector similarity search, deterministic local embedder. | Complete (Verified) |
| **Phase 3: Agent Framework & Grounding** | Pi Coding Agent (`pi-coding-agent`) runner, ToolRegistry, KnowledgeRetrievalTool, Citation extraction, hallucination refusal guardrails. | Complete (Verified) |
| **Phase 4: Skills & Ship 30 Generator** | 7 growth skills, Ship 30 for 30 essay engine (1,000–1,500 words), Growth Action Plans, decision frameworks. | Complete (Verified) |
| **Phase 5: Artifact Viewer & Security** | Claude-style dual-pane viewer, Formatted/Raw/Citations tabs, iframe sandboxing (`allow-scripts`), server-side regex sanitizer. | Complete (Verified) |
| **Phase 6: Verification & Test Suite** | 64 automated pytest tests passing, Vite TypeScript build passing, UI manual test plan. | Complete (Verified) |
| **Phase 7: Evaluator Packaging & Handoff** | One-command Docker startup, complete documentation (`PRD.md`, `design.md`, `architecture.md`, `README.md`), agent transcripts, demo video script. | Complete (Verified) |
