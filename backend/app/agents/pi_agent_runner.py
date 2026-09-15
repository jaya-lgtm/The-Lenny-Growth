import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session

# Official Pi Coding Agent imports
from pi_agent.agent import Agent, AgentConfig, AssistantResponse, Usage, ToolCall, ToolResult
from pi_agent.tools.registry import ToolRegistry
from pi_agent.tools.base import Tool
from pi_agent.sandbox import Sandbox

# Local application imports
from app.providers.base import BaseLLMProvider
from app.retrieval.retriever import VectorRetriever
from app.retrieval.schemas import RetrievalResult
from app.agents.schemas import AgentContext, AgentOutput, SourceCitation
from app.agents.prompts import (
    GROUNDED_QA_SYSTEM_PROMPT,
    GROUNDED_QA_CONTEXT_TEMPLATE,
)

logger = logging.getLogger("backend.agents.pi_runner")


class PiLLMAdapter:
    """
    Adapts our multi-provider abstraction (Ollama, OpenAI, Anthropic, Mock)
    to satisfy the Pi Coding Agent's LLMProvider protocol.
    """

    def __init__(self, provider: BaseLLMProvider):
        self._provider = provider
        self.name = provider.provider_name
        self.model = provider.model_name

    @property
    def supports_streaming(self) -> bool:
        return False

    def complete(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> AssistantResponse:
        """
        Translates Pi Coding Agent messages into our provider interface
        and returns an AssistantResponse.
        """
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, str):
                prompt_parts.append(f"{role.capitalize()}: {content}")
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        prompt_parts.append(f"{role.capitalize()}: {part['text']}")
            elif "results" in msg:
                for tr in msg["results"]:
                    out = getattr(tr, "output", str(tr))
                    prompt_parts.append(f"Tool Result ({getattr(tr, 'name', 'tool')}): {out}")

        compiled_prompt = "\n\n".join(prompt_parts) if prompt_parts else "Please assist."

        llm_response = self._provider.generate(
            prompt=compiled_prompt,
            system_prompt=system,
        )

        tokens = llm_response.token_usage or {}
        usage = Usage(
            input_tokens=tokens.get("prompt_tokens", 0),
            output_tokens=tokens.get("completion_tokens", 0),
        )

        return AssistantResponse(
            text=llm_response.content,
            usage=usage,
            stop_reason="end_turn",
        )


class PiGroundedAgent:
    """
    Grounded Q&A Agent powered by the Pi Coding Agent framework (pi_agent).
    
    Provides:
    - ToolRegistry holding knowledge retrieval tools connected to PostgreSQL pgvector
    - Sandboxed execution via Pi Agent's Sandbox
    - Dynamic agent configuration with grounded system prompts
    - Full source citation tracking and limitation enforcement
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        retriever: Optional[VectorRetriever] = None,
        db: Optional[Session] = None,
        workspace_root: str = ".",
    ):
        self.provider = provider
        self.retriever = retriever or VectorRetriever()
        self.db = db
        self.workspace_root = workspace_root

    def run(
        self,
        context: AgentContext,
        retrieval_results: Optional[List[RetrievalResult]] = None,
    ) -> AgentOutput:
        """
        Executes a grounded Q&A turn through the Pi Coding Agent engine.
        """
        captured_results: List[RetrievalResult] = list(retrieval_results or [])

        # 1. Define tool for Pi Agent to query transcript knowledge
        def retrieve_transcript_knowledge(args: Dict[str, Any], sandbox: Sandbox) -> str:
            query = args.get("query", context.user_question)
            top_k = int(args.get("top_k", 4))
            if self.db:
                results = self.retriever.retrieve(
                    db=self.db,
                    query=query,
                    top_k=top_k,
                )
                captured_results.extend(results)
                if not results:
                    return "No matching transcripts found in the knowledge base."
                lines = []
                for r in results:
                    guest = r.metadata.get("guest") or "Unknown Guest"
                    rel_path = r.metadata.get("relative_path") or "N/A"
                    lines.append(
                        f"Title: {r.title} | Guest: {guest} | File: {rel_path} | Match: {r.similarity*100:.1f}%\n"
                        f"URL: {r.source_url or 'N/A'}\n"
                        f"Content: {r.content.strip()}"
                    )
                return "\n\n---\n\n".join(lines)
            return "Database connection unavailable for retrieval tool."

        knowledge_tool = Tool(
            name="retrieve_transcript_knowledge",
            description="Query Lenny's Podcast and Newsletter transcript repository for evidence on product, growth, activation, retention, and PMF.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Topic or search query to locate transcript evidence."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of transcript chunks to retrieve (default: 4)."
                    }
                },
                "required": ["query"]
            },
            handler=retrieve_transcript_knowledge,
            mutating=False,
        )

        # 2. Build ToolRegistry and Sandbox
        registry = ToolRegistry([knowledge_tool])
        sandbox = Sandbox(root=Path(self.workspace_root))

        # 3. Configure Pi Coding Agent
        pi_provider = PiLLMAdapter(self.provider)
        config = AgentConfig(
            model=self.provider.model_name,
            provider=self.provider.provider_name,
            max_iterations=5,
            stream=False,
            system_prompt=GROUNDED_QA_SYSTEM_PROMPT,
        )

        agent = Agent(
            provider=pi_provider,
            registry=registry,
            sandbox=sandbox,
            config=config,
        )

        # 4. Construct prompt with evidence and history context
        evidence_lines = []
        citations: List[SourceCitation] = []
        for i, res in enumerate(captured_results, 1):
            guest = res.metadata.get("guest") or res.metadata.get("guest_name") or "Unknown Guest"
            rel_path = res.metadata.get("relative_path") or "transcripts/unknown"
            pub_date = res.metadata.get("publish_date") or res.metadata.get("published_at")
            excerpt = res.content.strip()[:240] + "..." if len(res.content.strip()) > 240 else res.content.strip()

            content_snippet = res.content.strip()[:650] + ("..." if len(res.content.strip()) > 650 else "")
            evidence_lines.append(
                f"[{i}] Source: \"{res.title}\" with {guest} ({res.source_type})\n"
                f"File: {rel_path}\n"
                f"URL: {res.source_url or 'N/A'}\n"
                f"Content: {content_snippet}\n"
            )
            citations.append(
                SourceCitation(
                    title=res.title,
                    source_type=res.source_type,
                    source_url=res.source_url,
                    guest=guest,
                    relative_path=rel_path,
                    publish_date=str(pub_date) if pub_date else None,
                    chunk_index=res.chunk_index,
                    excerpt=excerpt,
                    similarity=res.similarity,
                    metadata=res.metadata or {},
                )
            )

        evidence_block = "\n".join(evidence_lines) if evidence_lines else "No transcripts retrieved."

        history_lines = []
        for msg in context.conversation_history[-4:]:
            role = msg.get("role", "user").capitalize()
            text = msg.get("content", "").strip()
            if role == "Assistant" and len(text) > 250:
                text = text[:250] + "..."
            history_lines.append(f"{role}: {text}")
        history_block = "\n".join(history_lines) if history_lines else "None (starting new topic)"

        prompt = GROUNDED_QA_CONTEXT_TEMPLATE.format(
            evidence_block=evidence_block,
            history_block=history_block,
            user_question=context.user_question,
        )

        # 5. Execute user turn through Pi Coding Agent
        response_text = agent.run(user_input=prompt)

        return AgentOutput(
            content=response_text,
            provider=self.provider.provider_name,
            model=self.provider.model_name,
            retrieval_count=len(citations),
            sources=citations,
            raw_metadata={
                "framework": "pi-coding-agent",
                "iterations": len(agent.messages),
                "total_usage": {
                    "input_tokens": agent.total_usage.input_tokens,
                    "output_tokens": agent.total_usage.output_tokens,
                }
            },
        )
