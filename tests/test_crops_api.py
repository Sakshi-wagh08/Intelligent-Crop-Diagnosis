from fastapi.testclient import TestClient


def test_get_crops_returns_seeded_crops(client: TestClient):
    """Verifies /api/v1/crops returns seeded crops with their associated diseases."""
    response = client.get("/api/v1/crops")
    assert response.status_code == 200
    crops = response.json()
    assert len(crops) >= 3

    crop_names = [c["name"] for c in crops]
    assert "Tomato" in crop_names
    assert "Potato" in crop_names
    assert "Rice" in crop_names

    # Verify diseases attached to Tomato
    tomato = next(c for c in crops if c["name"] == "Tomato")
    disease_names = [d["disease_name"] for d in tomato["diseases"]]
    assert "Early Blight" in disease_names
    assert "Late Blight" in disease_names
