from fastapi.testclient import TestClient


def test_api_calculate_substitution_success(client: TestClient):
    """Verifies POST /api/v1/merchants/calculate-substitution endpoint."""
    payload = {
        "reference_dose_Qr": 0.80,
        "reference_concentration_Cr": 75.0,
        "substitute_concentration_Cs": 80.0,
        "reference_dose_unit": "kg/acre",
        "concentration_unit_Cr": "%",
        "concentration_unit_Cs": "%",
        "field_area_acres": 2.0,
        "package_size_str": "1 kg",
        "product_price": 460.0,
    }
    response = client.post("/api/v1/merchants/calculate-substitution", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["reference_dose_Qr"] == 0.80
    assert data["reference_concentration_Cr"] == 75.0
    assert data["substitute_concentration_Cs"] == 80.0
    assert data["substitute_dose_Qs"] == 0.75  # 0.80 * (75/80)
    assert data["total_substitute_quantity"] == 1.50  # 0.75 * 2.0
    assert data["packages_needed"] == 2  # ceil(1.50 / 1.0)
    assert data["estimated_total_cost"] == 920.0  # 2 * 460.0
    assert "Qs = Qr * (Cr / Cs)" in data["formula_expression"]


def test_api_calculate_substitution_invalid_dosage(client: TestClient):
    """Verifies POST /api/v1/merchants/calculate-substitution rejects negative dosages."""
    payload = {
        "reference_dose_Qr": -0.80,  # Invalid negative
        "reference_concentration_Cr": 75.0,
        "substitute_concentration_Cs": 80.0,
    }
    response = client.post("/api/v1/merchants/calculate-substitution", json=payload)
    assert response.status_code == 422 or response.status_code == 400


def test_api_substitute_and_rank_success(client: TestClient):
    """Verifies POST /api/v1/merchants/substitute-and-rank end-to-end dealer discovery and ranking."""
    # Farmer coordinates near Ramanagara, Karnataka
    payload = {
        "latitude": 12.7210,
        "longitude": 77.2810,
        "crop_name": "Tomato",
        "disease_name": "Early Blight",
        "active_ingredient": "Mancozeb",
        "reference_dose_Qr": 0.80,
        "reference_concentration_Cr": 75.0,
        "reference_dose_unit": "kg/acre",
        "prescribed_application_method": "Foliar Spray",
        "field_area_acres": 1.0,
        "max_distance_km": 60.0,
        "weights": {
            "price": 0.40,
            "distance": 0.35,
            "stock": 0.25,
        },
        "allow_demo": True,
    }
    response = client.post("/api/v1/merchants/substitute-and-rank", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["total_merchants_searched"] >= 2
    assert data["total_eligible_products"] >= 1
    assert "DEMONSTRATION NOTICE" in data["demonstration_advisory"]

    # Validate ranked offerings
    ranked = data["ranked_offerings"]
    assert len(ranked) >= 1
    assert ranked[0]["rank"] == 1
    assert ranked[0]["composite_score"] > 0.0
    assert ranked[0]["substitute_dose_Qs"] > 0.0
    assert ranked[0]["packages_needed"] >= 1
    assert ranked[0]["estimated_total_cost"] > 0.0
    assert ranked[0]["score_breakdown"]["weights_applied"]["price"] == 0.40
    assert len(ranked[0]["ranking_explanation"]) > 10

    # Validate that ranks are strictly ordered
    scores = [item["composite_score"] for item in ranked]
    assert scores == sorted(scores, reverse=True)


def test_api_substitute_and_rank_ineligible_candidates_segregation(client: TestClient):
    """Verifies that out-of-stock, crop-mismatch, and granular formulations are placed in ineligibles."""
    payload = {
        "latitude": 12.7210,
        "longitude": 77.2810,
        "crop_name": "Tomato",
        "disease_name": "Early Blight",
        "active_ingredient": "Mancozeb",
        "reference_dose_Qr": 0.80,
        "reference_concentration_Cr": 75.0,
        "max_distance_km": 100.0,
    }
    response = client.post("/api/v1/merchants/substitute-and-rank", json=payload)
    assert response.status_code == 200
    data = response.json()

    ineligible = data["ineligible_candidates"]
    assert len(ineligible) >= 2

    # Check for specific ineligibility reasons
    reasons = [item["ineligibility_reason"] for item in ineligible]
    assert any("Out of stock" in r for r in reasons)
    assert any("Not officially registered for crop 'Tomato'" in r for r in reasons)


def test_api_substitute_and_rank_tiny_radius_returns_no_merchants(client: TestClient):
    """Verifies response when search radius is too small to find any agro-dealers."""
    payload = {
        "latitude": 0.0,
        "longitude": 0.0,
        "crop_name": "Tomato",
        "disease_name": "Early Blight",
        "active_ingredient": "Mancozeb",
        "reference_dose_Qr": 0.80,
        "reference_concentration_Cr": 75.0,
        "max_distance_km": 1.0,
    }
    response = client.post("/api/v1/merchants/substitute-and-rank", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NO_MERCHANTS_WITHIN_RADIUS"
    assert data["total_merchants_searched"] == 0
    assert len(data["ranked_offerings"]) == 0


def test_api_substitute_and_rank_invalid_coordinates(client: TestClient):
    """Verifies HTTP 422 when latitude or longitude coordinates exceed WGS 84 bounds."""
    payload = {
        "latitude": 105.0,  # Invalid latitude (> 90.0)
        "longitude": 77.0,
        "crop_name": "Tomato",
        "disease_name": "Early Blight",
        "active_ingredient": "Mancozeb",
        "reference_dose_Qr": 0.80,
        "reference_concentration_Cr": 75.0,
    }
    response = client.post("/api/v1/merchants/substitute-and-rank", json=payload)
    assert response.status_code == 422


def test_api_merchant_profile_and_product_catalog(client: TestClient):
    """Verifies GET /api/v1/merchants/{id}, GET /api/v1/merchants/{id}/products, and product detail."""
    # 1. Get Merchant 1 profile
    res_m = client.get("/api/v1/merchants/1")
    assert res_m.status_code == 200
    m_data = res_m.json()
    assert m_data["id"] == 1
    assert "Kisan Seva Kendra" in m_data["name"]
    assert len(m_data["products"]) > 0

    # 2. Get Merchant 1 products catalog
    res_mp = client.get("/api/v1/merchants/1/products")
    assert res_mp.status_code == 200
    products = res_mp.json()
    assert isinstance(products, list)
    assert len(products) > 0
    prod_id = products[0]["id"]

    # 3. Get single product detail
    res_p = client.get(f"/api/v1/merchants/products/{prod_id}")
    assert res_p.status_code == 200
    p_data = res_p.json()
    assert p_data["id"] == prod_id
    assert p_data["price"] > 0
    assert p_data["concentration_Cs"] > 0


def test_api_merchant_not_found(client: TestClient):
    """Verifies HTTP 404 when querying non-existent merchant or product."""
    res_m = client.get("/api/v1/merchants/99999")
    assert res_m.status_code == 404

    res_p = client.get("/api/v1/merchants/products/99999")
    assert res_p.status_code == 404


def test_api_calculate_substitution_cross_basis_rejection(client: TestClient):
    """Verifies HTTP 400 when attempting cross-basis (% w/w to % w/v) without density."""
    payload = {
        "reference_dose_Qr": 0.80,
        "reference_concentration_Cr": 75.0,
        "substitute_concentration_Cs": 23.0,
        "reference_dose_unit": "kg/acre",
        "concentration_unit_Cr": "% w/w",   # Mass basis
        "concentration_unit_Cs": "% w/v",   # Volume basis
    }
    response = client.post("/api/v1/merchants/calculate-substitution", json=payload)
    assert response.status_code == 400
    assert "density" in response.json()["detail"].lower()


def test_api_calculate_substitution_mass_volume_package_mismatch(client: TestClient):
    """Verifies HTTP 400 when mass dosage (kg/acre) is paired with volume package (mL) without density."""
    payload = {
        "reference_dose_Qr": 0.80,
        "reference_concentration_Cr": 75.0,
        "substitute_concentration_Cs": 75.0,
        "reference_dose_unit": "kg/acre",  # Mass
        "package_size_str": "500 mL",       # Volume
    }
    response = client.post("/api/v1/merchants/calculate-substitution", json=payload)
    assert response.status_code == 400
    assert "unit mismatch" in response.json()["detail"].lower()

