# Product Requirements Document (PRD) & Forward Deployment Brief
## The Lenny Growth Assistant

> **Note**: For the complete document with detailed specifications and acceptance criteria, see [docs/prd.md](file:///docs/prd.md).

---

## 1. Forward Deployment Discovery Brief

### 1.1 User Persona & Problem Statement
* **Primary Users**: Product Managers, Startup Founders, Growth Leads, and Strategy Operators.
* **Job to be Done**: Turn strategic product and growth wisdom from over 300 Lenny's Podcast and Newsletter episodes into tactical, evidence-backed deliverables (playbooks, checklists, frameworks, experiment plans, essays, and interactive components) without having to manually read hundreds of transcripts or craft complex prompts.
* **Pain Points Removed**:
  1. Information Fragmentation across 300+ episodes.
  2. Hallucination and lack of trust in generic LLMs.
  3. Prompt fatigue and formatting friction.
  4. Context switching across disparate tools.

### 1.2 Measurable Success Metrics
1. **Evidence Grounding Ratio**: $\ge 95\%$ of substantive claims trace directly to indexed ChatPRD transcript chunks with valid guest and YouTube links.
2. **Unsupported Query Safety**: $100\%$ of out-of-domain questions acknowledge knowledge boundaries rather than hallucinating.
3. **Artifact Isolation & Safety**: Zero iframe same-origin escapes (`allow-same-origin` is strictly omitted).
4. **Evaluator Time-to-First-Value**: $< 3$ minutes from clone to first generated artifact using `docker compose up -d`.
5. **Ship 30 Compliance**: 100% of generated Ship 30 essays fall strictly within 1,000–1,500 words with hook, 3 structured parts, and takeaways.

### 1.3 Strategic Assumptions & Scope Decisions
* **Corpus Authority**: ChatPRD community archive is the authoritative source.
* **Evaluator Machine Constraints**: Ships with zero-setup `mock` provider and local 768-dim deterministic embedder, alongside native `ollama` (`llama3.2:3b`) and cloud providers.
* **Scope Included**: FastAPI, PostgreSQL 16 + pgvector, Pi Coding Agent framework, 7 growth skills, Ship 30 essays, Claude-style Artifact Viewer, sandboxed iframe isolation.
* **Scope Excluded**: Arbitrary Python execution in containers, live web scraping, multi-tenant billing.

### 1.4 Acceptance Criteria Summary
* **Grounded Q&A**: Every answer includes episode title, guest name, timestamped YouTube link, match score, and verbatim quote.
* **Ship 30 Essays**: Generates 1,000–1,500 word essays with hook, 3 parts, and takeaways.
* **Artifact Viewer**: Provides Formatted, Raw Source, and Evidence tabs with copy/export actions.
* **Security**: Iframe sandboxing with `sandbox="allow-scripts"` and strictly no `allow-same-origin`.
* **Resilience**: Explicit HTTP 503 on provider outage with zero silent switching.

---

For complete flows and Given-When-Then test cases, refer to [docs/prd.md](file:///docs/prd.md).
