# The Lenny Growth Assistant
> **Forward Deployed Engineer Take-Home Assignment Deliverable**

**The Lenny Growth Assistant** is an enterprise-grade AI workspace that turns insights from Lenny's Podcast and Newsletter into evidence-grounded product decisions, actionable growth plans, and reusable artifacts.

Powered by **PostgreSQL 16 with pgvector**, the **Pi Coding Agent framework (`pi-coding-agent`)**, and the real **ChatPRD Lenny's Podcast Transcripts** corpus, the assistant synthesizes real podcast episodes to answer product questions and generate structured deliverables across 7 specialized growth skills.

---

## Required Deliverables Index

| # | Deliverable | Location in Repository | Summary |
| :-: | :--- | :--- | :--- |
| **1** | **Public GitHub Repository** | Root workspace | Clean project structure, containerized, zero committed secrets. |
| **2** | **README.md** | [README.md](file:///README.md) | Architecture overview, setup, env config, test execution, troubleshooting. |
| **3** | **Product Requirements (PRD)** | [PRD.md](file:///PRD.md) & [docs/prd.md](file:///docs/prd.md) | User persona, problem framing, success metrics, scope, flows, acceptance criteria. |
| **4** | **Design Specification** | [design.md](file:///design.md) & [docs/design.md](file:///docs/design.md) | UI/UX principles, information architecture, 7 interaction states, responsive layouts, a11y. |
| **5** | **Architecture Document** | [architecture.md](file:///architecture.md) & [docs/architecture.md](file:///docs/architecture.md) | DB schema, sequence flows, Docker topology, logging, resilience & failure matrices. |
| **6** | **Coding Agent Transcripts** | [agent_transcripts/](file:///agent_transcripts/) & [SUMMARY.md](file:///agent_transcripts/SUMMARY.md) | Chronological development logs, failed attempts, and how they were corrected. |
| **7** | **Automated & Manual Tests** | [tests/](file:///tests/) & [tests/manual_test_plan.md](file:///tests/manual_test_plan.md) | 64 passing automated tests + step-by-step UI manual test plan. |
| **8** | **Demo Video Script & Guide** | [DEMO_SCRIPT.md](file:///DEMO_SCRIPT.md) & [docs/demo_video_guide.md](file:///docs/demo_video_guide.md) | 2–3 minute timed talk track, camera setup checklist, YouTube submission steps. |

---

## 1. Key Capabilities

* **Evidence-Grounded Product Reasoning**: Synthesizes answers strictly from indexed episode chunks with verbatim quotes, speaker attributions, YouTube timestamps, and match scores.
* **Specialized Growth Skills**:
  * **Activation & Onboarding**: Setup moments, aha moments, habit formation, and friction reduction.
  * **Retention & Cohort Analysis**: Retention curve plateaus, churn mitigation, and engagement loops.
  * **Product-Market Fit (PMF)**: Sean Ellis 40% threshold evaluations, leading PMF signals, and retention indicators.
  * **Growth Loops & Funnels**: Compounding viral, content, and paid acquisition loops vs linear funnels.
  * **Experimentation & Strategy**: ICE/RICE scoring, hypothesis formulation, and strategic roadmaps.
* **Structured Artifact Generation**:
  * 🚀 **Growth Action Plans**: Phased execution playbooks with owners, metrics, and cadences.
  * 📝 **Ship 30 Essays**: Longform essays (1,000–1,500 words) with clear hooks, structured parts, actionable takeaways, and source citations.
  * 🎯 **Growth Frameworks**: Systematic decision matrices and mental models.
  * ✅ **Audit Checklists**: Objective readiness criteria and verification items.
  * 🧪 **Experiment Plans**: Hypotheses, variants, metrics, guardrails, and sample sizes.
  * 🧭 **Strategy Documents**: Vision, target audience, competitive moats, and resource allocation.
  * 💻 **Interactive HTML/CSS Components**: Scoped, self-contained widgets and diagrams.
* **Secure Artifact Viewer**:
  * Slide-over UI with Formatted Markdown, Raw Source, and Evidence & Citations tabs.
  * **Sandboxed Iframe Isolation**: HTML/CSS artifacts render strictly inside an `iframe` with `sandbox="allow-scripts"` and **no** `allow-same-origin`.
  * Copy to clipboard and one-click `.md` / `.html` artifact export.
  * Immutable artifacts: regeneration generates a new version with a distinct UUID.
* **Multi-Provider Architecture (Zero Silent Fallbacks)**:
  * **Mock**: Deterministic, offline provider for rapid testing and evaluation.
  * **Ollama**: Local, private LLM execution (`llama3.2:3b` / `llama3.1:8b`) and embeddings (`nomic-embed-text`).
  * **Cloud Providers**: OpenAI (`gpt-4o-mini`) and Anthropic (`claude-3-5-sonnet`) when configured.
  * Explicit HTTP 503 error returned if a requested provider is unavailable.

---

## 2. Technology Stack

* **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons
* **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic v2, pgvector
* **Agent Framework**: Pi Coding Agent framework (`pi-coding-agent`), Claude Agent SDK (`claude-agent-sdk`)
* **Database**: PostgreSQL 16 with pgvector extension (`pgvector/pgvector:pg16`)
* **Database Migrations**: Alembic (`001_initial_schema`, `002_documents_and_chunks`, `003_artifacts`)
* **Orchestration**: Docker Compose
* **Testing**: Pytest, HTTPX, Starlette TestClient (64 automated tests)

---

## 3. Quick Start (Docker Compose)

### 3.1 Clone & Setup Environment
```bash
git clone <repository-url>
cd lenny

# Copy environment variables
cp .env.example .env
```

### 3.2 Build & Launch Services
```bash
docker compose up --build -d
```

This starts 3 containers:
* `lenny_growth_db`: PostgreSQL 16 with pgvector on port `5432`
* `lenny_growth_backend`: FastAPI application on port `8000` (auto-runs migrations)
* `lenny_growth_frontend`: Vite development server on port `5173`

### 3.3 Verify Service Health
```bash
# Check container status
docker compose ps

# Check backend health
curl http://localhost:8000/api/health
```

### 3.4 Access the Application
* **Frontend Web Application**: [http://localhost:5173](http://localhost:5173)
* **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Runtime System Config**: [http://localhost:8000/api/config](http://localhost:8000/api/config)

---

## 4. Knowledge Base & Ingestion Pipeline

The knowledge base is built from the real **ChatPRD Lenny's Podcast Transcripts** repository:
[https://github.com/ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts)

The corpus contains over 300 episode transcripts with metadata (`guest`, `title`, `youtube_url`, `publish_date`, `description`, `keywords`).

### Run Ingestion Pipeline
```bash
# Ingest using local deterministic embedder (fastest for offline testing)
python -m ingestion.pipeline --clone --provider local

# Ingest using local Ollama nomic-embed-text
python -m ingestion.pipeline --provider ollama

# Refresh corpus idempotently (updates existing docs, preserves user sessions)
python -m ingestion.pipeline --force --provider local
```

Or trigger ingestion dynamically via the API:
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"provider": "local", "clone": true}'
```

---

## 5. Database Migrations

Migrations are managed with Alembic and run automatically when the backend container starts.

```bash
# Apply migrations to the latest version
docker compose exec backend alembic upgrade head

# Check current revision
docker compose exec backend alembic current

# Run migrations manually on host (if running outside Docker)
alembic upgrade head
```

### Migration History
* `001_initial_schema`: `sessions` and `messages` tables with cascade relationships.
* `002_documents_and_chunks`: `documents` and `document_chunks` tables with 768-dimension vector embeddings and HNSW cosine index.
* `003_artifacts`: `artifacts` table with `artifact_type`, `content_format`, `schema_version`, and cascade delete tied to `session_id`.

---

## 6. Provider Configuration

Configure providers in your `.env` file:

```ini
# Active Provider: 'mock', 'ollama', 'openai', 'anthropic'
LLM_PROVIDER=ollama

# Local Ollama Configuration (Bridge to Host Machine)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:3b

# Embedding Provider: 'local', 'ollama', 'openai'
EMBEDDING_PROVIDER=local
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Cloud API Keys (Optional)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

> **Note**: If a provider is selected in the UI but unavailable, the API returns an explicit HTTP 503 error. The system never silently falls back to an unselected provider.

---

## 7. Demo Prompts & Expected Outputs

| Mode / Skill | Sample Prompt | Expected Output |
| :--- | :--- | :--- |
| **Grounded Q&A** | *"What are the three components of activation according to Lenny's guests?"* | Synthesized answer citing Casey Winters / Eric Simons with excerpts and match percentages. |
| **Growth Action Plan** | *"Create a growth action plan for user onboarding and activation"* | Phased 30-60-90 day playbook with milestones, metrics, and owner assignments. |
| **Retention Framework** | *"Develop a retention cohort framework for a B2B SaaS platform"* | Structured framework with baseline retention curves and churn mitigation tactics. |
| **Audit Checklist** | *"Build an audit checklist to evaluate product market fit"* | Actionable checklist with verification criteria and Sean Ellis 40% metric thresholds. |
| **Experiment Plan** | *"Design an experiment plan to test onboarding friction reduction"* | Formal experiment spec with hypothesis, control/variant designs, and sample sizes. |
| **Ship 30 Essay** | *"Write a Ship 30 essay on why retention is the silent killer of startups"* | 1,000–1,500 word structured essay with hook, thematic sections, takeaways, and citations. |
| **Strategy Document** | *"Write a strategy document for product-led growth expansion"* | Executive strategy brief with target audience, competitive moats, and roadmaps. |
| **HTML/CSS Component** | *"Generate an interactive growth loops visualizer component"* | Sandboxed interactive HTML component rendered safely inside an isolated iframe. |

---

## 8. API Reference

### Chat & Agent
* `POST /api/chat` — Submit a message with optional `mode` (`auto`, `grounded_qa`, `growth_action_plan`, `ship30_essay`, `framework`, `checklist`, `experiment_plan`, `strategy_doc`, `html_css`) and `provider`. Returns assistant message and optional generated `artifact`.

### Artifacts
* `GET /api/artifacts/{id}` — Retrieve an artifact by UUID. Optional `session_id` query param enforces session boundaries.
* `GET /api/artifacts/session/{session_id}` — List all artifacts created in a specific conversation session.
* `DELETE /api/artifacts/{id}` — Delete a specific artifact.

### Sessions & Messages
* `POST /api/sessions` — Create a conversation.
* `GET /api/sessions` — List conversations sorted by `updated_at DESC`.
* `PATCH /api/sessions/{id}` — Rename conversation.
* `DELETE /api/sessions/{id}` — Delete conversation (cascades strictly to its artifacts and messages).
* `GET /api/sessions/{id}/messages` — List messages in a session.

### System & Health
* `GET /api/health` — Database connectivity status (`ok` or `degraded`).
* `GET /api/config` — Non-secret runtime settings and provider availability statuses.

---

## 9. Security & Sandboxed Isolation

* **Sandboxed Iframe**: All HTML/CSS artifacts are rendered inside an `iframe` with `sandbox="allow-scripts"` and **without** `allow-same-origin`.
* **No DOM Injection**: Generated HTML is never injected into the main React DOM.
* **Server-Side Sanitization**: The backend strips external script tags (`<script src="...">`), parent/top navigation attempts (`window.top.location`, `window.parent.document`), meta refresh tags, and external form actions.
* **Cross-Session Access Control**: Artifact retrieval and deletion support session scoping to prevent cross-session tampering.

---

## 10. Automated Tests & Manual Test Plan

### Run Automated Tests
Run the complete 64-test test suite inside Docker:

```bash
docker compose exec backend pytest tests/ -v
```

Or run directly on the host:
```bash
python -m pytest tests/ -v
```

```text
============================= test session starts ==============================
collected 64 items

tests/test_agent_framework.py::test_required_framework_imports_and_sdk_presence PASSED
tests/test_agent_framework.py::test_pi_grounded_agent_execution PASSED
tests/test_agent_framework.py::test_grounded_qa_agent_delegation_to_pi_agent PASSED
tests/test_agent_framework.py::test_chat_turn_persists_pi_agent_framework_metadata PASSED
tests/test_chat_agent.py::test_chat_turn_persists_messages_and_metadata PASSED
tests/test_chat_agent.py::test_chat_unsupported_question_acknowledges_limitation PASSED
tests/test_milestone3_artifacts.py::test_artifact_creation_and_persistence PASSED
tests/test_milestone3_artifacts.py::test_artifact_immutability_on_regeneration PASSED
tests/test_milestone3_artifacts.py::test_artifact_session_cascade_deletion PASSED
tests/test_milestone3_artifacts.py::test_intent_routing PASSED
tests/test_milestone3_artifacts.py::test_ship30_essay_word_count_and_structure PASSED
tests/test_milestone3_artifacts.py::test_html_sanitization_and_isolation PASSED
tests/test_milestone3_artifacts.py::test_cross_session_artifact_access_denied PASSED
...
======================== 64 passed, 12 warnings in 8.86s ========================
```

### Manual Test Plan
For step-by-step end-to-end UI testing scenarios, consult the [UI Manual Test Plan](file:///tests/manual_test_plan.md).

---

## 11. Troubleshooting & FAQs

### 1. `503 Provider Unavailable` when using Ollama
* **Cause**: Ollama daemon is not running on your host machine, or the configured model is not downloaded.
* **Fix**:
  1. Verify Ollama is running on host: `ollama list`.
  2. Pull the model: `ollama pull llama3.2:3b`.
  3. Ensure Docker can reach the host: verify `OLLAMA_BASE_URL=http://host.docker.internal:11434`.
  4. If running without Ollama, select the deterministic `mock` provider in the UI for instant offline testing.

### 2. Port Conflicts on 5432, 8000, or 5173
* **Fix**: Edit `.env` to assign non-conflicting host ports:
  ```ini
  POSTGRES_PORT=5433
  BACKEND_PORT=8001
  FRONTEND_PORT=5174
  ```

### 3. Database Connection Failure
* **Fix**: Verify the `lenny_growth_db` container is healthy:
  ```bash
  docker compose ps
  docker compose logs db
  ```

---

## 12. Attributions & Acknowledgments

* **Transcript Source Attribution**: Transcripts are sourced from the public community archive maintained by ChatPRD at `https://github.com/ChatPRD/lennys-podcast-transcripts`. Content rights for Lenny's Podcast and Newsletter remain with Lenny Rachitsky and respective podcast guests.
* **Agent Framework**: Built with the Pi Coding Agent framework (`pi-coding-agent`) and Claude Agent SDK.
