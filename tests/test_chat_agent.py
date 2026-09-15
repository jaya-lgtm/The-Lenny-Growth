import uuid
import pytest
from fastapi import status
from app.models.document import DocumentModel
from app.models.chunk import DocumentChunkModel
from app.models.message import MessageModel
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate
from ingestion.embedder import DeterministicLocalEmbedder


@pytest.fixture
def chat_seed_data(db_session):
    """Seed test database with an active session and activation knowledge."""
    embedder = DeterministicLocalEmbedder(dim=768)

    # 1. Create a session
    session = SessionService.create_session(
        db=db_session, session_in=SessionCreate(title="Activation Chat")
    )

    # 2. Create sample document & chunk
    doc = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Demo Episode: Activation Secrets",
        source_url="https://example.com/demo-activation",
        content_hash="hash-chat-seed-1",
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        content="Activation is the milestone where users experience the core value proposition.",
        token_count=11,
        embedding=embedder.embed_text("Activation is the milestone where users experience the core value proposition."),
    )
    db_session.add(chunk)
    db_session.commit()

    return {"session": session, "doc": doc, "chunk": chunk}


def test_chat_turn_persists_messages_and_metadata(client, chat_seed_data, monkeypatch):
    """POST /api/chat records user and assistant messages with source citations."""
    session_id = str(chat_seed_data["session"].id)

    # Force mock LLM provider and deterministic embedder for offline test isolation
    from app.providers.cloud import MockLLMProvider
    from ingestion.embedder import DeterministicLocalEmbedder
    monkeypatch.setattr("app.agents.orchestrator.get_llm_provider", lambda name=None: MockLLMProvider())
    monkeypatch.setattr("app.retrieval.embeddings.get_query_embedder", lambda: DeterministicLocalEmbedder(dim=768))

    res = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "How do I improve user activation?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    assert data["session_id"] == session_id
    msg = data["message"]
    assert msg["role"] == "assistant"
    assert "activation" in msg["content"].lower()
    assert msg["provider"] == "mock"
    assert "message_metadata" in msg
    assert msg["message_metadata"]["model"] == "mock-growth-v1"
    assert "sources" in msg["message_metadata"]

    # Verify message history contains both user and assistant messages
    hist_res = client.get(f"/api/sessions/{session_id}/messages")
    assert hist_res.status_code == status.HTTP_200_OK
    history = hist_res.json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "How do I improve user activation?"
    assert history[1]["role"] == "assistant"


def test_chat_unsupported_question_acknowledges_limitation(client, chat_seed_data, monkeypatch):
    """When query is unsupported and retrieval is empty, agent honestly acknowledges limitation."""
    session_id = str(chat_seed_data["session"].id)

    from app.providers.cloud import MockLLMProvider
    monkeypatch.setattr("app.agents.orchestrator.get_llm_provider", lambda name=None: MockLLMProvider())

    # Mock empty retrieval
    monkeypatch.setattr("app.retrieval.retriever.VectorRetriever.retrieve", lambda *args, **kwargs: [])

    res = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "What is the speed of light in vacuum?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    content = data["message"]["content"]
    assert "not find sufficient evidence" in content.lower()
    assert data["message"]["message_metadata"]["retrieval_count"] == 0
    assert len(data["message"]["message_metadata"]["sources"]) == 0


def test_chat_invalid_session_id_returns_404(client):
    """Chatting with non-existent session ID returns 404."""
    random_id = str(uuid.uuid4())
    res = client.post(
        "/api/chat",
        json={"session_id": random_id, "message": "Hello there"},
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_chat_empty_message_returns_422(client, chat_seed_data):
    """Empty message body returns 422 validation error."""
    session_id = str(chat_seed_data["session"].id)
    res = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "   "},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_config_endpoint(client):
    """GET /api/config returns non-secret runtime configuration."""
    res = client.get("/api/config")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "active_llm_provider" in data
    assert "available_providers" in data
    assert len(data["available_providers"]) >= 4
    providers = [p["provider"] for p in data["available_providers"]]
    assert "ollama" in providers
    assert "openai" in providers
    assert "anthropic" in providers
    assert "mock" in providers


def test_post_ingest_endpoint(client, tmp_path, monkeypatch):
    """POST /api/ingest triggers ingestion and returns summary statistics."""
    doc_file = tmp_path / "sample.md"
    doc_file.write_text(
        "---\ntitle: \"API Ingest Doc\"\nsource_type: \"newsletter\"\n---\n\nSample content for API test.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")

    res = client.post("/api/ingest", json={"provider": "local", "force": True})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "completed"
    assert data["discovered"] >= 1
    assert data["inserted"] >= 1


def test_chat_greeting_does_not_force_citations(client, chat_seed_data, monkeypatch):
    """When query is a casual greeting like 'hi', assistant responds naturally without transcript citations."""
    session_id = str(chat_seed_data["session"].id)

    from app.providers.cloud import MockLLMProvider
    monkeypatch.setattr("app.agents.orchestrator.get_llm_provider", lambda name=None: MockLLMProvider())

    res = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "hi"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    msg = data["message"]
    assert msg["role"] == "assistant"
    assert "lenny growth assistant" in msg["content"].lower()
    assert msg["message_metadata"]["retrieval_count"] == 0
    assert len(msg["message_metadata"]["sources"]) == 0

