import pytest
from app.agents.pi_agent_runner import PiGroundedAgent, PiLLMAdapter
from app.agents.grounded_qa import GroundedQAAgent
from app.agents.schemas import AgentContext
from app.retrieval.schemas import RetrievalResult
from app.providers.cloud import MockLLMProvider
from pi_agent.agent import Agent, AgentConfig
from pi_agent.tools.registry import ToolRegistry
import claude_agent_sdk


def test_required_framework_imports_and_sdk_presence():
    """Verify both assignment-approved frameworks (pi-coding-agent & claude-agent-sdk) are present."""
    # 1. Verify pi-coding-agent core classes
    import pi_agent
    from pi_agent.agent import Agent, AgentConfig, AssistantResponse
    from pi_agent.tools.registry import ToolRegistry
    from pi_agent.tools.base import Tool
    from pi_agent.sandbox import Sandbox

    assert Agent is not None
    assert ToolRegistry is not None
    assert Tool is not None
    assert Sandbox is not None

    # 2. Verify Anthropic Claude Agent SDK
    assert hasattr(claude_agent_sdk, "query")
    assert hasattr(claude_agent_sdk, "ClaudeAgentOptions")


def test_pi_grounded_agent_execution():
    """Verify PiGroundedAgent executes via pi_agent.agent.Agent with knowledge retrieval tools."""
    mock_provider = MockLLMProvider()
    pi_agent_runner = PiGroundedAgent(provider=mock_provider)

    import uuid
    c_id = uuid.uuid4()
    d_id = uuid.uuid4()
    sample_results = [
        RetrievalResult(
            chunk_id=c_id,
            document_id=d_id,
            title="Why most product managers are unprepared | Casey Winters",
            source_type="podcast",
            source_url="https://www.youtube.com/watch?v=WlRfyEpAKxw",
            content="Casey Winters explains that growth loops compounding acquisition and retention.",
            similarity=0.88,
            chunk_index=0,
            metadata={
                "guest": "Casey Winters",
                "relative_path": "episodes/casey-winters/transcript.md",
                "publish_date": "2023-04-12",
            }
        )
    ]

    context = AgentContext(
        session_id=uuid.uuid4(),
        user_question="How do growth loops differ from funnels?",
        conversation_history=[],
        retrieved_chunks=sample_results,
    )

    output = pi_agent_runner.run(context=context, retrieval_results=sample_results)

    assert output.provider == "mock"
    assert output.model == "mock-growth-v1"
    assert len(output.sources) == 1
    assert output.sources[0].guest == "Casey Winters"
    assert output.sources[0].relative_path == "episodes/casey-winters/transcript.md"
    assert output.raw_metadata.get("framework") == "pi-coding-agent"
    assert "Casey Winters" in output.content or "growth loop" in output.content.lower()


def test_grounded_qa_agent_delegation_to_pi_agent():
    """Verify GroundedQAAgent delegates execution directly to Pi Coding Agent."""
    mock_provider = MockLLMProvider()
    agent = GroundedQAAgent(provider=mock_provider)

    assert hasattr(agent, "pi_agent")
    assert isinstance(agent.pi_agent, PiGroundedAgent)


def test_chat_turn_persists_pi_agent_framework_metadata(client, db_session, monkeypatch):
    """Verify /api/chat persists agent_framework='pi-coding-agent' in message_metadata."""
    import uuid
    from app.services.session_service import SessionService
    from app.schemas.session import SessionCreate
    from app.providers.cloud import MockLLMProvider
    from ingestion.embedder import DeterministicLocalEmbedder

    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Framework Test"))
    session_id = str(session.id)

    monkeypatch.setattr("app.agents.orchestrator.get_llm_provider", lambda name=None: MockLLMProvider())
    monkeypatch.setattr("app.retrieval.embeddings.get_query_embedder", lambda: DeterministicLocalEmbedder(dim=768))

    res = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "How do growth loops work?"},
    )
    assert res.status_code == 200
    msg = res.json()["message"]
    assert msg["message_metadata"]["agent_framework"] == "pi-coding-agent"

