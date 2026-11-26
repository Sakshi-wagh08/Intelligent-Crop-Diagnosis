from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verifies root endpoint returns project metadata and documentation paths."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "version" in data
    assert data["status"] == "online"
    assert "/api/v1/docs" in data["documentation"]


def test_health_endpoint(client: TestClient):
    """Verifies /api/v1/health reports system status and database diagnostic fields."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "components" in data
    assert "connected" in data["database"]
    assert "postgis_enabled" in data["database"]
