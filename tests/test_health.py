from unittest.mock import MagicMock
from fastapi import status
from app.db.session import get_db
from app.main import app


def test_health_success(client):
    """Verify health endpoint returns 200 and database connected when healthy."""
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "The Lenny Growth Assistant" in data["service"]


def test_health_failure_when_database_unavailable(client):
    """Verify health endpoint returns 503 when database connectivity fails."""
    # Mock broken DB session
    def _broken_get_db():
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Connection to PostgreSQL failed: timeout")
        yield mock_db

    app.dependency_overrides[get_db] = _broken_get_db
    try:
        response = client.get("/api/health")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert "Database connectivity check failed" in data["error"]["message"]
        assert data["error"]["details"]["status"] == "degraded"
    finally:
        app.dependency_overrides.clear()
