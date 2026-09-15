import uuid
import time
from fastapi import status


def test_create_session_default_title(client):
    """Creating a session without a title defaults to 'New Conversation'."""
    response = client.post("/api/sessions", json={})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    # verify valid UUID
    uuid.UUID(data["id"])
    assert data["title"] == "New Conversation"
    assert "created_at" in data
    assert "updated_at" in data


def test_create_session_custom_title(client):
    """Creating a session with a custom title."""
    title = "SaaS Retention Strategies Discussion"
    response = client.post("/api/sessions", json={"title": title})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == title


def test_list_sessions_sorted_by_updated_at_desc(client):
    """Sessions must be returned sorted by updated_at descending."""
    res1 = client.post("/api/sessions", json={"title": "Session 1"})
    time.sleep(0.01)
    res2 = client.post("/api/sessions", json={"title": "Session 2"})

    id1 = res1.json()["id"]
    id2 = res2.json()["id"]

    list_res = client.get("/api/sessions")
    assert list_res.status_code == status.HTTP_200_OK
    session_list = list_res.json()

    # Session 2 was created later, so it should appear before Session 1
    ids = [s["id"] for s in session_list]
    assert ids.index(id2) < ids.index(id1)


def test_get_session_by_id(client):
    """Retrieve an existing session by ID."""
    res = client.post("/api/sessions", json={"title": "Activation Deep Dive"})
    session_id = res.json()["id"]

    get_res = client.get(f"/api/sessions/{session_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == session_id
    assert get_res.json()["title"] == "Activation Deep Dive"


def test_get_missing_session_returns_404(client):
    """Requesting a non-existent session returns 404 with standardized error format."""
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/sessions/{random_id}")
    assert res.status_code == status.HTTP_404_NOT_FOUND
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()


def test_rename_session(client):
    """Renaming a session updates its title."""
    res = client.post("/api/sessions", json={"title": "Initial Title"})
    session_id = res.json()["id"]

    patch_res = client.patch(
        f"/api/sessions/{session_id}", json={"title": "Updated Growth Plan"}
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["title"] == "Updated Growth Plan"

    # Confirm via get
    get_res = client.get(f"/api/sessions/{session_id}")
    assert get_res.json()["title"] == "Updated Growth Plan"


def test_rename_session_empty_title_fails(client):
    """Renaming a session with an empty or whitespace title returns 422."""
    res = client.post("/api/sessions", json={"title": "Valid Title"})
    session_id = res.json()["id"]

    patch_res = client.patch(f"/api/sessions/{session_id}", json={"title": "   "})
    assert patch_res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = patch_res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_delete_session_and_cascade_messages(client):
    """Deleting a session cascades and deletes associated messages."""
    res = client.post("/api/sessions", json={"title": "To Be Deleted"})
    session_id = res.json()["id"]

    # Add a message to this session
    msg_res = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"role": "user", "content": "Hello Lenny Assistant"},
    )
    assert msg_res.status_code == status.HTTP_201_CREATED

    # Delete the session
    del_res = client.delete(f"/api/sessions/{session_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify session is gone
    check_session = client.get(f"/api/sessions/{session_id}")
    assert check_session.status_code == status.HTTP_404_NOT_FOUND

    # Verify messages endpoint for deleted session returns 404
    check_messages = client.get(f"/api/sessions/{session_id}/messages")
    assert check_messages.status_code == status.HTTP_404_NOT_FOUND


def test_auto_title_session_on_first_chat(client):
    """A session created as 'New Conversation' gets automatically titled when user sends a chat message."""
    create_res = client.post("/api/sessions", json={})
    assert create_res.status_code == status.HTTP_201_CREATED
    session_id = create_res.json()["id"]
    assert create_res.json()["title"] == "New Conversation"

    # Send first turn
    chat_res = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "How do I improve user activation?",
            "provider": "mock",
        },
    )
    assert chat_res.status_code == status.HTTP_200_OK

    # Check that session was auto-titled in DB
    session_res = client.get(f"/api/sessions/{session_id}")
    assert session_res.status_code == status.HTTP_200_OK
    assert session_res.json()["title"] == "Improve user activation"

