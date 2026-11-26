import io
from PIL import Image
from fastapi.testclient import TestClient


def create_test_leaf_image_bytes() -> bytes:
    """Generates an in-memory PNG leaf image."""
    img = Image.new("RGB", (300, 300), color=(40, 160, 45))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_api_fusion_pathologies_endpoint(client: TestClient):
    """Verifies GET /api/v1/fusion/pathologies returns verified agricultural entries."""
    response = client.get("/api/v1/fusion/pathologies")
    assert response.status_code == 200
    pathologies = response.json()
    assert isinstance(pathologies, list)
    assert len(pathologies) >= 3

    crops = {p["crop"] for p in pathologies}
    assert "Tomato" in crops
    assert "Potato" in crops
    assert "Rice" in crops


def test_api_fusion_recommend_direct_success(client: TestClient):
    """Verifies POST /api/v1/fusion/recommend with direct pre-diagnosed telemetry."""
    payload = {
        "crop_name": "Tomato",
        "crop_stage": "Vegetative",
        "latitude": 13.0,
        "longitude": 77.0,
        "days_to_harvest": 20,
        "diagnosed_disease": "Early Blight",
        "diagnostic_confidence": 0.92,
        "allow_demo": False,
    }
    response = client.post("/api/v1/fusion/recommend", data=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["recommendation_available"] is True
    assert data["status"] == "SUCCESS"
    assert data["treatment"]["active_ingredient"] == "Mancozeb"
    assert data["dosage_breakdown"]["final_prescribed_dose"] == 0.80
    assert data["safety_assessment"]["is_safe_to_apply"] is True


def test_api_fusion_recommend_phi_rejection(client: TestClient):
    """Verifies POST /api/v1/fusion/recommend suppresses dosage when PHI is violated."""
    payload = {
        "crop_name": "Rice",
        "crop_stage": "Tillering",
        "latitude": 13.0,
        "longitude": 77.0,
        "days_to_harvest": 5,  # Tricyclazole mandates 30-day PHI
        "diagnosed_disease": "Blast",
        "diagnostic_confidence": 0.89,
    }
    response = client.post("/api/v1/fusion/recommend", data=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["recommendation_available"] is False
    assert data["status"] == "REJECTED_PHI_VIOLATION"
    assert data["safety_assessment"]["is_safe_to_apply"] is False
    assert data["safety_assessment"]["phi_check_passed"] is False


def test_api_fusion_recommend_healthy_crop(client: TestClient):
    """Verifies POST /api/v1/fusion/recommend with healthy leaf returns no chemical treatment."""
    payload = {
        "crop_name": "Tomato",
        "crop_stage": "Vegetative",
        "latitude": 13.0,
        "longitude": 77.0,
        "diagnosed_disease": "healthy",
        "diagnostic_confidence": 0.99,
    }
    response = client.post("/api/v1/fusion/recommend", data=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["recommendation_available"] is True
    assert data["status"] == "HEALTHY_NO_TREATMENT_NEEDED"
    assert data["treatment"] is None
    assert data["dosage_breakdown"] is None


def test_api_fusion_recommend_with_image_upload(client: TestClient):
    """Verifies POST /api/v1/fusion/recommend accepts leaf image file upload."""
    img_bytes = create_test_leaf_image_bytes()
    files = {"image": ("test_leaf.png", img_bytes, "image/png")}
    data = {
        "crop_name": "Tomato",
        "crop_stage": "Vegetative",
        "latitude": 13.0,
        "longitude": 77.0,
        "diagnosed_disease": "Early Blight",  # Fallback if no weights trained
        "diagnostic_confidence": 0.85,
    }
    response = client.post("/api/v1/fusion/recommend", data=data, files=files)
    assert response.status_code == 200
    res_data = response.json()
    assert "telemetry_summary" in res_data
    assert res_data["telemetry_summary"]["crop"] == "Tomato"
