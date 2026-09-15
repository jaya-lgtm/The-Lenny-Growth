# Coding Agent Transcript: Milestone 3 — Agent Framework Integration & Grounding

## Task Objective
Integrate the official Pi Coding Agent framework (`pi-coding-agent`) with `ToolRegistry` and `KnowledgeRetrievalTool`, assemble system prompts enforcing transcript attribution, and implement graceful limitation acknowledgment for ungrounded queries.

---

## Attempt 1: Pi Coding Agent Framework Tool Registration
* **Agent Action**: Integrated Pi Coding Agent by inheriting from `pi_agent.tools.base.Tool`:
  ```python
  class KnowledgeRetrievalTool(Tool):
      name = "retrieve_knowledge"
      description = "Search indexed Lenny Podcast transcripts"
      ...
  ```
* **Issue Encountered**:
  The Pi Agent orchestrator expects tool execution to return structured dictionary output conforming to Pi Agent's `ToolResult` interface, but initial code returned a raw string. When serialized into the assistant message turn, the metadata dictionary dropped citation attributes.
* **Diagnosis**:
  Pi Agent runner was stripping non-standard fields on `ToolResult.output`.
* **Correction & Fix**:
  1. Updated `KnowledgeRetrievalTool.execute` to package structured citations into a dedicated `SourceCitation` schema:
     ```python
     return ToolResult(
         output=json.dumps({"citations": [c.model_dump() for c in citations], "context": context_text}),
         name=self.name
     )
     ```
  2. Implemented `PiLLMAdapter` to bridge our multi-provider abstraction (`Ollama`, `Mock`, `OpenAI`, `Anthropic`) into the Pi Agent completion protocol.
  3. Added `test_agent_framework.py` validating that every turn executes through `PiGroundedAgent` and records `agent_framework: "pi-coding-agent"` in message metadata.

---

## Attempt 2: Hallucination on Out-of-Domain Questions
* **Agent Action**: Initial system prompt tested with query: *"What is the recipe for chocolate chip cookies?"*
* **Issue Encountered**:
  The LLM generated a plausible recipe despite no relevant chunks existing in the database.
* **Diagnosis**:
  When vector similarity scores were low (<0.35), the retriever still passed the closest 3 chunks, and the LLM attempted to synthesize an answer regardless of relevance.
* **Correction & Fix**:
  1. Implemented a strict cosine similarity score threshold (0.50 minimum).
  2. Enhanced system prompt guardrail:
     ```text
     If the provided transcript excerpts do not contain sufficient evidence to answer the question,
     you MUST explicitly acknowledge:
     "I cannot find evidence for this in the available Lenny's Podcast transcripts."
     Do NOT extrapolate or invent facts.
     ```
  3. Verified with automated test `test_chat_agent.py::test_chat_unsupported_question_acknowledges_limitation`.
