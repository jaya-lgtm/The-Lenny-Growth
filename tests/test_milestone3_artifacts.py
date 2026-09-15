import uuid
import pytest
from fastapi import status
from app.services.session_service import SessionService
from app.services.artifact_service import ArtifactService, ArtifactNotFoundException
from app.schemas.session import SessionCreate
from app.schemas.artifact import ArtifactCreate
from app.agents.skills.router import IntentRouter
from app.agents.skills.generators import sanitize_html_content, generate_mock_artifact
from app.agents.schemas import SourceCitation
from app.providers.cloud import MockLLMProvider
from ingestion.embedder import DeterministicLocalEmbedder


def test_artifact_creation_and_persistence(db_session):
    """Artifact is persisted with content_format and schema_version."""
    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Artifact Test Session"))
    
    art_in = ArtifactCreate(
        session_id=session.id,
        artifact_type="growth_action_plan",
        content_format="markdown",
        schema_version="v1.0",
        title="Test Growth Action Plan",
        content="# Plan Content\n\n- Milestone 1",
        artifact_metadata={"word_count": 10, "author": "Lenny Growth Assistant"},
    )
    artifact = ArtifactService.create_artifact(db=db_session, session_id=session.id, artifact_in=art_in)

    assert artifact.id is not None
    assert artifact.session_id == session.id
    assert artifact.artifact_type == "growth_action_plan"
    assert artifact.content_format == "markdown"
    assert artifact.schema_version == "v1.0"
    assert artifact.title == "Test Growth Action Plan"
    assert "Plan Content" in artifact.content

    # Retrieve artifact
    fetched = ArtifactService.get_artifact(db=db_session, artifact_id=artifact.id)
    assert fetched.id == artifact.id
    assert fetched.artifact_metadata["word_count"] == 10


def test_artifact_immutability_on_regeneration(db_session):
    """Regenerating creates a new immutable artifact instead of overwriting."""
    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Immutability Session"))

    art1 = ArtifactService.create_artifact(
        db=db_session,
        session_id=session.id,
        artifact_in=ArtifactCreate(
            session_id=session.id,
            artifact_type="framework",
            content_format="markdown",
            schema_version="v1.0",
            title="Version 1",
            content="Initial framework draft",
        ),
    )

    art2 = ArtifactService.create_artifact(
        db=db_session,
        session_id=session.id,
        artifact_in=ArtifactCreate(
            session_id=session.id,
            artifact_type="framework",
            content_format="markdown",
            schema_version="v1.0",
            title="Version 2",
            content="Regenerated framework draft with more details",
        ),
    )

    assert art1.id != art2.id
    artifacts = ArtifactService.list_session_artifacts(db=db_session, session_id=session.id)
    assert len(artifacts) == 2
    # Ensure art1 content was not mutated
    fresh_art1 = ArtifactService.get_artifact(db=db_session, artifact_id=art1.id)
    assert fresh_art1.content == "Initial framework draft"


def test_artifact_session_cascade_deletion(db_session):
    """Deleting a session cascades to its artifacts only, preserving other sessions."""
    s1 = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Session 1"))
    s2 = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Session 2"))

    art1 = ArtifactService.create_artifact(
        db=db_session,
        session_id=s1.id,
        artifact_in=ArtifactCreate(
            session_id=s1.id,
            artifact_type="checklist",
            title="S1 Checklist",
            content="Checklist for S1",
        ),
    )

    art2 = ArtifactService.create_artifact(
        db=db_session,
        session_id=s2.id,
        artifact_in=ArtifactCreate(
            session_id=s2.id,
            artifact_type="checklist",
            title="S2 Checklist",
            content="Checklist for S2",
        ),
    )

    # Delete session 1
    SessionService.delete_session(db=db_session, session_id=s1.id)

    # art1 should no longer exist
    with pytest.raises(ArtifactNotFoundException):
        ArtifactService.get_artifact(db=db_session, artifact_id=art1.id)

    # art2 must still exist
    fetched_art2 = ArtifactService.get_artifact(db=db_session, artifact_id=art2.id)
    assert fetched_art2.id == art2.id


def test_intent_routing():
    """Verify IntentRouter routes explicit modes and detects keywords in auto mode."""
    # Explicit routing
    mode, name = IntentRouter.classify("any message", explicit_mode="growth_action_plan")
    assert mode == "growth_action_plan"
    assert name == "Growth Action Plan"

    mode, name = IntentRouter.classify("any message", explicit_mode="ship30_essay")
    assert mode == "ship30_essay"
    assert name == "Ship 30 Essay"

    # Auto keyword detection
    mode, _ = IntentRouter.classify("Can you write a Ship 30 essay on activation loops?", explicit_mode="auto")
    assert mode == "ship30_essay"

    mode, _ = IntentRouter.classify("Build an audit checklist for user onboarding", explicit_mode="auto")
    assert mode == "checklist"

    mode, _ = IntentRouter.classify("Create an experiment plan to test templates", explicit_mode="auto")
    assert mode == "experiment_plan"

    mode, _ = IntentRouter.classify("What is the difference between funnels and loops?", explicit_mode="auto")
    assert mode == "grounded_qa"


def test_ship30_essay_word_count_and_structure():
    """Ship 30 essay targets 1,000-1,500 words with hook, structured sections, and takeaways."""
    sample_citation = SourceCitation(
        title="Why most product managers are unprepared | Casey Winters",
        source_type="podcast",
        source_url="https://www.youtube.com/watch?v=WlRfyEpAKxw",
        guest="Casey Winters",
        relative_path="episodes/casey-winters/transcript.md",
        similarity=0.91,
        excerpt="Casey Winters explains that growth loops compound acquisition and retention.",
    )

    essay_data = generate_mock_artifact(
        mode="ship30_essay",
        query="The Power of Growth Loops",
        citations=[sample_citation],
    )

    content = essay_data["content"]
    body_text = content.split("## Evidence Traceability")[0].strip()
    body_word_count = len(body_text.split())
    full_word_count = len(content.split())

    # Verify strict requirement: 1,000 <= word_count <= 1,500
    assert 1000 <= body_word_count <= 1500, f"Body word count was {body_word_count}"
    assert 1000 <= full_word_count <= 1500, f"Full word count was {full_word_count}"

    assert "Casey Winters" in content
    assert "Part 1" in content
    assert "Part 2" in content
    assert "Part 3" in content
    assert "Key Takeaways" in content
    assert "Evidence Traceability & Grounding" in content
    assert essay_data["content_format"] == "markdown"
    assert essay_data["schema_version"] == "v1.0"



def test_html_sanitization_and_isolation():
    """Sanitizer blocks external script sources, parent DOM access, and window navigation for sandboxed iframe safety."""
    malicious_html = """
    <div>
      <script src="https://evil.com/malicious.js"></script>
      <meta http-equiv="refresh" content="0;url=https://evil.com" />
      <base href="https://evil.com" />
      <button onclick="window.top.location='https://phishing.com'">Click Top</button>
      <button onclick="window.parent.document.cookie='stolen'">Click Parent</button>
      <a href="https://evil.com" target="_top">Top Link</a>
      <form action="https://evil.com/submit">Form</form>
      <h2>Safe Component</h2>
    </div>
    """
    sanitized = sanitize_html_content(malicious_html)
    assert "evil.com/malicious.js" not in sanitized
    assert "http-equiv=\"refresh\"" not in sanitized.lower()
    assert "<base" not in sanitized.lower()
    assert "window.top.location" not in sanitized
    assert "window.parent.document" not in sanitized
    assert "target=\"_top\"" not in sanitized
    assert 'action="https://evil.com/submit"' not in sanitized
    assert "Safe Component" in sanitized
    assert "<!DOCTYPE html>" in sanitized



def test_chat_generates_and_persists_artifact(client, db_session, monkeypatch):
    """POST /api/chat with mode='growth_action_plan' persists artifact and returns it in response."""
    from app.models.document import DocumentModel
    from app.models.chunk import DocumentChunkModel

    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Chat Artifact Test"))
    session_id = str(session.id)

    # Seed test knowledge so retrieval succeeds
    embedder = DeterministicLocalEmbedder(dim=768)
    doc = DocumentModel(
        id=uuid.uuid4(),
        source_type="podcast",
        title="Activation Secrets | Casey Winters",
        source_url="https://youtube.com/watch?v=demo",
        content_hash="hash-art-test-1",
        doc_metadata={"guest": "Casey Winters", "relative_path": "episodes/casey/transcript.md"},
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        content="Activation milestones require setup, aha, and habit moments.",
        token_count=10,
        embedding=embedder.embed_text("Activation milestones require setup, aha, and habit moments."),
        chunk_metadata={"guest": "Casey Winters", "relative_path": "episodes/casey/transcript.md"},
    )
    db_session.add(chunk)
    db_session.flush()

    # Seed mock provider
    monkeypatch.setattr("app.agents.orchestrator.get_llm_provider", lambda name=None: MockLLMProvider())
    monkeypatch.setattr("app.retrieval.embeddings.get_query_embedder", lambda: DeterministicLocalEmbedder(dim=768))

    res = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "Create a Growth Action Plan for activation milestones",
            "provider": "mock",
            "mode": "growth_action_plan",
        },
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    assert data["session_id"] == session_id
    assert "artifact" in data
    artifact = data["artifact"]
    assert artifact is not None
    assert artifact["artifact_type"] == "growth_action_plan"
    assert artifact["content_format"] == "markdown"
    assert artifact["schema_version"] == "v1.0"
    assert "Phase 1" in artifact["content"]
    assert "artifact_id" in data["message"]["message_metadata"]

    # Verify retrieval by ID endpoint
    art_id = artifact["id"]
    get_res = client.get(f"/api/artifacts/{art_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == art_id

    # Verify list by session endpoint
    list_res = client.get(f"/api/artifacts/session/{session_id}")
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) >= 1


def test_chat_invalid_mode_returns_422(client, db_session):
    """Invalid mode in chat request returns 422 unprocessable entity."""
    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Invalid Mode Test"))
    res = client.post(
        "/api/chat",
        json={
            "session_id": str(session.id),
            "message": "Hello",
            "mode": "invalid_mode_123",
        },
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_missing_artifact_returns_404(client):
    """GET /api/artifacts/{missing_id} returns 404."""
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/artifacts/{random_id}")
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json()["error"]["code"] == "ARTIFACT_NOT_FOUND"


def test_unsupported_question_does_not_generate_artifact(client, db_session, monkeypatch):
    """When query is unsupported and retrieval is empty, no artifact is created."""
    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Unsupported Test"))
    session_id = str(session.id)

    monkeypatch.setattr("app.agents.orchestrator.get_llm_provider", lambda name=None: MockLLMProvider())
    monkeypatch.setattr("app.retrieval.retriever.VectorRetriever.retrieve", lambda *args, **kwargs: [])

    res = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "What is quantum physics entanglement?",
            "mode": "growth_action_plan",
        },
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["artifact"] is None
    assert "not find sufficient evidence" in data["message"]["content"].lower()


def test_chat_empty_content_returns_422(client, db_session):
    """Empty or whitespace-only message returns 422."""
    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Empty Msg Test"))
    res = client.post(
        "/api/chat",
        json={
            "session_id": str(session.id),
            "message": "   ",
            "mode": "growth_action_plan",
        },
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_chat_invalid_session_returns_404(client):
    """Chat with non-existent session UUID returns 404."""
    random_session_id = str(uuid.uuid4())
    res = client.post(
        "/api/chat",
        json={
            "session_id": random_session_id,
            "message": "Valid prompt for non-existent session",
            "mode": "growth_action_plan",
        },
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_ollama_unavailability_explicit_error(client, db_session, monkeypatch):
    """When Ollama is requested but unavailable, an explicit error is returned with NO silent fallback."""
    from app.providers.base import ProviderUnavailableException

    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Ollama Failure Test"))

    def mock_ollama_fail(*args, **kwargs):
        raise ProviderUnavailableException(provider="ollama", message="Connection refused at http://localhost:11434")

    monkeypatch.setattr("app.agents.orchestrator.get_llm_provider", mock_ollama_fail)

    res = client.post(
        "/api/chat",
        json={
            "session_id": str(session.id),
            "message": "Explain retention curves",
            "provider": "ollama",
        },
    )
    assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    error_data = res.json()["error"]
    assert "ollama" in error_data["message"].lower() or "connection refused" in error_data["message"].lower()


def test_artifact_persistence_failure_handling(db_session, monkeypatch):
    """Artifact service properly rolls back and raises when DB persistence fails."""
    session = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Persistence Fail Test"))

    art_in = ArtifactCreate(
        session_id=session.id,
        artifact_type="checklist",
        title="Failing Checklist",
        content="Some content",
    )

    # Monkeypatch db.flush to simulate failure
    def mock_flush():
        raise Exception("Database transaction failed")

    monkeypatch.setattr(db_session, "flush", mock_flush)

    with pytest.raises(Exception, match="Database transaction failed"):
        ArtifactService.create_artifact(db=db_session, session_id=session.id, artifact_in=art_in)


def test_cross_session_artifact_access_denied(client, db_session):
    """Accessing an artifact using a mismatched session_id returns 403 Forbidden."""
    s1 = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Owner Session"))
    s2 = SessionService.create_session(db=db_session, session_in=SessionCreate(title="Attacker Session"))

    art = ArtifactService.create_artifact(
        db=db_session,
        session_id=s1.id,
        artifact_in=ArtifactCreate(
            session_id=s1.id,
            artifact_type="framework",
            title="Private Framework",
            content="Confidential content",
        ),
    )

    # Scoped get with correct session succeeds
    res_ok = client.get(f"/api/artifacts/{art.id}?session_id={s1.id}")
    assert res_ok.status_code == status.HTTP_200_OK

    # Scoped get with mismatched session returns 403
    res_denied = client.get(f"/api/artifacts/{art.id}?session_id={s2.id}")
    assert res_denied.status_code == status.HTTP_403_FORBIDDEN
    assert res_denied.json()["error"]["code"] == "CROSS_SESSION_ACCESS_DENIED"

    # Scoped delete with mismatched session returns 403
    res_del_denied = client.delete(f"/api/artifacts/{art.id}?session_id={s2.id}")
    assert res_del_denied.status_code == status.HTTP_403_FORBIDDEN



