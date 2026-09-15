# Coding Agent Transcripts & Development Log Summary
## The Lenny Growth Assistant

---

## 1. Overview

This directory contains sanitized, chronological engineering transcripts and development logs generated during the implementation of **The Lenny Growth Assistant**.

In accordance with the Forward Deployed Engineer evaluation rubric, these logs document:
* Core engineering decisions and architecture evolution.
* **Failed attempts, failure modes, and bugs encountered**.
* **How each failure was diagnosed, corrected, and verified**.
* Secret sanitization and operational handoff considerations.

---

## 2. Transcript Index

| Transcript | Focus Area | Key Failure Mode & Resolution |
| :--- | :--- | :--- |
| [01_scaffolding_and_schema.md](file:///agent_transcripts/01_scaffolding_and_schema.md) | FastAPI, PostgreSQL, Alembic | DB migration race condition on startup -> resolved via Docker healthchecks and backoff retry. Cascade foreign key deletion bug -> fixed via explicit DB-level `ondelete="CASCADE"`. |
| [02_ingestion_and_vector_pipeline.md](file:///agent_transcripts/02_ingestion_and_vector_pipeline.md) | ChatPRD Transcripts, Embeddings | 4096 vs 768 vector dimension mismatch -> resolved by standardizing on 768-dim embeddings. Oversized chunks -> resolved via recursive 500-token chunking with 50-token overlap. |
| [03_agent_framework_and_grounding.md](file:///agent_transcripts/03_agent_framework_and_grounding.md) | Pi Coding Agent, Grounding | ToolResult citation dropping -> resolved via structured `SourceCitation` schemas. Out-of-domain hallucination -> resolved with 0.50 cosine similarity threshold and explicit refusal prompt. |
| [04_skills_and_ship30_generator.md](file:///agent_transcripts/04_skills_and_ship30_generator.md) | 7 Growth Skills, Ship 30 Essays | Ship 30 essay word count under-generation (~450 words) -> resolved via structural section minimums (1,000–1,500w). Intent classification collision -> weighted intent routing. |
| [05_artifact_viewer_and_security_sandbox.md](file:///agent_transcripts/05_artifact_viewer_and_security_sandbox.md) | Claude Slide-Over Viewer, Security | XSS vulnerability in `dangerouslySetInnerHTML` -> replaced with isolated `<iframe>` (`sandbox="allow-scripts"` without `allow-same-origin`). Overwritten drafts -> immutable UUID versioning. |
| [06_resilience_and_provider_toggle.md](file:///agent_transcripts/06_resilience_and_provider_toggle.md) | Multi-Provider, Ollama, Resilience | Silent fallback masks model failures -> eliminated silent fallback in favor of explicit HTTP 503 error envelopes. Docker container unable to reach host Ollama -> configured `host.docker.internal`. |

---

## 3. Verification & Secret Sanitization Notice
All transcripts and configuration logs in this directory have been audited to ensure:
1. Zero secrets or API keys are committed.
2. Real ChatPRD transcript data and episode citations are preserved.
3. Every corrective action is validated by the 64 automated tests in the `tests/` directory.
