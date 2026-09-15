# Grounded Q&A Agent Architecture & Prompts
## The Lenny Growth Assistant

The Lenny Growth Assistant agent layer is designed to act as an intelligent, evidence-grounded research and execution partner for product and growth professionals.

---

## 1. Agent Orchestration Architecture

The system executes chat requests using the **Pi Coding Agent framework (`pi-coding-agent`)**, integrated with an intent routing layer for specialized growth skills:

```
User Message + Session ID + Optional Mode
                 │
                 ▼
         ChatOrchestrator
                 │
       ┌─────────┴─────────────────────────────┐
       ▼                                       ▼
1. Save User Message in DB          2. VectorRetriever (pgvector)
       │                                       │
       │                                Retrieve top-k chunks
       │                                with source metadata
       ▼                                       │
3. Intent Router ◄─────────────────────────────┘
   (Auto or Explicit Skill Mode)
       │
       ▼
4. GroundedQAAgent (PiGroundedAgent)
   • pi_agent.agent.Agent
   • pi_agent.tools.registry.ToolRegistry
   • KnowledgeRetrievalTool
   • pi_agent.sandbox.Sandbox
       │
       ▼
5. Multi-Provider LLM (Mock / Ollama / OpenAI / Anthropic)
       │
       ▼
6. Format Citations & Limitations
       │
       ▼
7. Persist Assistant Message in PostgreSQL
   (metadata: provider, model, sources, agent_framework="pi-coding-agent")
       │
       ▼
8. If Skill Mode Requested -> Generate & Persist Immutable Artifact
   (growth_action_plan, ship30_essay, framework, checklist, experiment_plan, strategy_doc, html_css)
       │
       ▼
9. Update Session updated_at timestamp & Return Payload
```

---

## 2. Pi Coding Agent Framework Integration

The agent execution layer is built directly upon the official **Pi Coding Agent framework**:
* **`Agent` & `AgentConfig`**: Encapsulates agent state, system instructions, and execution loop.
* **`ToolRegistry` & `KnowledgeRetrievalTool`**: Registers semantic search tools so the agent can autonomously query PostgreSQL pgvector for transcript evidence.
* **`PiLLMAdapter`**: Adapts our multi-provider interface (`BaseLLMProvider`) to satisfy `pi_agent.llm.LLMProvider`, ensuring seamless execution with Ollama, OpenAI, Anthropic, or Mock.
* **`Sandbox`**: Manages isolated execution context for tools.
* **Metadata Persistence**: Every turn records `"agent_framework": "pi-coding-agent"` in `message.message_metadata`.

---

## 3. Grounding Policy & Evidentiary Rules

1. **Evidence First**: All factual assertions regarding Lenny's podcast episodes, guests, newsletter articles, frameworks, and benchmarks must derive from verified transcript evidence.
2. **Conservative Citation Validation**: A citation is only emitted if the specific chunk directly discusses the target concept (e.g. user activation, onboarding, time-to-first-value, retention). Tangential discussions (such as general leadership, team-building superpowers, or unrelated AI research) are strictly filtered out and never cited as evidence for growth queries.
3. **Zero Citation Padding**: One verified source produces exactly one citation. Zero valid sources produces a transparent statement of limitations rather than fabricated or loosely related citations.
4. **Honest Limitations**: If the knowledge base does not contain sufficient evidence for a query (e.g. out-of-domain questions or proprietary platform internal metrics), the agent does not guess. It explicitly states the limitation.
5. **No Hallucinated Sources**: The agent never fabricates guest names, URLs, quotes, or episode titles.
6. **Distinguish Reasoning from Transcripts**: When generalizing or synthesizing standard PM practices beyond the literal transcript excerpt, the agent explicitly demarcates transcript evidence from strategic recommendations.
7. **Clear, Medium-Length Structure**: Responses are structured with clear headings, bulleted action items, and skimmable takeaways without excessive verbosity.

---

## 4. Multi-Provider Abstraction

The assistant supports both local and cloud LLM execution via a unified `BaseLLMProvider` interface:

* **Offline & Test Mode**: `MockLLMProvider` returning deterministic grounded responses with source citations (default out-of-the-box configuration).
* **Local Inference**: `OllamaProvider` (`llama3.2:3b` via `http://host.docker.internal:11434`, with `DeterministicLocalEmbedder(768)` or `nomic-embed-text` embeddings).
* **Cloud Inference**:
  * `OpenAIProvider` (`gpt-4o-mini`).
  * `AnthropicProvider` (`claude-3-5-sonnet-20241022`).

### Failure Handling & Transparency
* If Ollama is selected but unreachable, the system returns a structured `503 Service Unavailable` error with actionable guidance (`"Cannot connect to Ollama at http://host.docker.internal:11434. Ensure Ollama is running ('ollama serve')"`).
* If a cloud provider is selected without an API key, it returns a structured `503 Service Unavailable` (`"OPENAI_API_KEY is not configured"`).
* The system **never silently switches providers** without reporting the provider in `message_metadata`.

---

## 5. Artifact Generation & Security Contract

When a specialized growth skill is invoked:
1. **Ship 30 Essay**: Synthesizes a 1,000–1,500 word longform essay with an executive hook, 3 structured parts, key takeaways, and verified podcast citations.
2. **Growth Action Plan & Experiment Backlog**: Produces structured markdown documents with prioritized experiments (ICE scoring, assumptions, and primary metrics).
3. **HTML/CSS Component**: Passes generated markup through `sanitize_html_content` to strip external scripts, `window.top.location`, and form hijacking.
4. **Artifact Viewer**: Renders HTML/CSS components inside an `iframe` with `sandbox="allow-scripts"` and **no** `allow-same-origin`.
5. **Immutability**: Every artifact is assigned a new UUID and persisted in PostgreSQL.
