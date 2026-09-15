import uuid
import time
from fastapi import status


def test_create_and_list_messages(client):
    """Creating and retrieving messages for a valid session."""
    session_res = client.post("/api/sessions", json={"title": "Messaging Test"})
    session_id = session_res.json()["id"]

    # 1. Create user message
    msg1_res = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"role": "user", "content": "How do I optimize retention?"},
    )
    assert msg1_res.status_code == status.HTTP_201_CREATED
    msg1_data = msg1_res.json()
    assert msg1_data["role"] == "user"
    assert msg1_data["content"] == "How do I optimize retention?"
    assert msg1_data["session_id"] == session_id
    assert "id" in msg1_data
    assert "created_at" in msg1_data

    # 2. Create assistant message
    msg2_res = client.post(
        f"/api/sessions/{session_id}/messages",
        json={
            "role": "assistant",
            "content": "Focus on your activation metric and core Aha moment first.",
            "provider": "ollama",
            "message_metadata": {"tokens": 15},
        },
    )
    assert msg2_res.status_code == status.HTTP_201_CREATED
    msg2_data = msg2_res.json()
    assert msg2_data["role"] == "assistant"
    assert msg2_data["provider"] == "ollama"

    # 3. List messages (should be sorted by created_at ascending)
    list_res = client.get(f"/api/sessions/{session_id}/messages")
    assert list_res.status_code == status.HTTP_200_OK
    messages = list_res.json()
    assert len(messages) == 2
    assert messages[0]["id"] == msg1_data["id"]
    assert messages[1]["id"] == msg2_data["id"]


def test_create_message_updates_parent_session_timestamp(client):
    """Creating a message must update the parent session's updated_at timestamp."""
    # Create two sessions
    res1 = client.post("/api/sessions", json={"title": "Older Session"})
    session1_id = res1.json()["id"]
    initial_updated_at = res1.json()["updated_at"]

    time.sleep(0.05)
    res2 = client.post("/api/sessions", json={"title": "Newer Session"})
    session2_id = res2.json()["id"]

    # Session 2 is currently newer than Session 1
    list_res1 = client.get("/api/sessions")
    assert list_res1.json()[0]["id"] == session2_id

    # Post a message into Session 1
    time.sleep(0.05)
    post_res = client.post(
        f"/api/sessions/{session1_id}/messages",
        json={"role": "user", "content": "Bumping this conversation!"},
    )
    assert post_res.status_code == status.HTTP_201_CREATED

    # Session 1's updated_at must have changed
    check_session = client.get(f"/api/sessions/{session1_id}")
    new_updated_at = check_session.json()["updated_at"]
    assert new_updated_at > initial_updated_at

    # Session 1 must now be at the very top of the session listing
    list_res2 = client.get("/api/sessions")
    assert list_res2.json()[0]["id"] == session1_id


def test_invalid_message_role_returns_422(client):
    """Invalid role outside ('user', 'assistant', 'system') returns 422."""
    session_res = client.post("/api/sessions", json={"title": "Role Test"})
    session_id = session_res.json()["id"]

    res = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"role": "moderator", "content": "Unauthorized role"},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_empty_message_content_returns_422(client):
    """Empty or whitespace-only message content returns 422."""
    session_res = client.post("/api/sessions", json={"title": "Empty Content Test"})
    session_id = session_res.json()["id"]

    res = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"role": "user", "content": "   "},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_create_message_for_missing_session_returns_404(client):
    """Creating a message for a non-existent session returns 404."""
    random_id = str(uuid.uuid4())
    res = client.post(
        f"/api/sessions/{random_id}/messages",
        json={"role": "user", "content": "Hello in the void"},
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


def test_get_messages_for_missing_session_returns_404(client):
    """Getting messages for a non-existent session returns 404."""
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/sessions/{random_id}/messages")
    assert res.status_code == status.HTTP_404_NOT_FOUND
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"
