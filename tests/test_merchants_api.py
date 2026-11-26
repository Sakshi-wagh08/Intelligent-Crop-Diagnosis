from fastapi.testclient import TestClient


def test_get_nearby_merchants_within_radius(client: TestClient):
    """Verifies /api/v1/merchants/nearby returns dealers within search radius with calculated distances."""
    # Farmer coordinates near Ramanagara, Karnataka
    farmer_lat = 12.7210
    farmer_lon = 77.2810

    response = client.get(
        f"/api/v1/merchants/nearby?latitude={farmer_lat}&longitude={farmer_lon}&max_distance_km=50.0"
    )
    assert response.status_code == 200
    merchants = response.json()
    assert len(merchants) > 0

    # Distances must be sorted ascending
    distances = [m["distance_km"] for m in merchants]
    assert distances == sorted(distances)

    # First merchant should be the one at Ramanagara (distance ~0.0 km)
    nearest = merchants[0]
    assert "Sri Lakshmi Agri Inputs" in nearest["merchant_name"]
    assert nearest["distance_km"] < 1.0


def test_get_nearby_merchants_filtered_by_active_ingredient(client: TestClient):
    """Verifies filtering nearby merchants by active ingredient ID."""
    farmer_lat = 12.7210
    farmer_lon = 77.2810

    # Active ingredient ID 1 is Mancozeb
    response = client.get(
        f"/api/v1/merchants/nearby?latitude={farmer_lat}&longitude={farmer_lon}&max_distance_km=100.0&active_ingredient_id=1"
    )
    assert response.status_code == 200
    merchants = response.json()
    assert len(merchants) > 0

    for m in merchants:
        assert m["brand_name"] is not None
        assert "Mancozeb" in m["brand_name"]
