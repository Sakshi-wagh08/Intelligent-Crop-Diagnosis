from fastapi.testclient import TestClient


def test_soil_telemetry_endpoint(client: TestClient):
    """Verifies /api/v1/soil/telemetry returns standardized SoilGrids parameters."""
    response = client.get("/api/v1/soil/telemetry?latitude=12.9716&longitude=77.5946")
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 12.9716
    assert data["longitude"] == 77.5946
    assert "parameters" in data
    params = data["parameters"]
    assert "pH" in params
    assert "organic_carbon_g_kg" in params
    assert "nitrogen_cg_kg" in params
    assert "soil_texture_class" in params
    assert "advisory_notice" in data
