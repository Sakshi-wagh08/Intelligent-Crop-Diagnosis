import io
from PIL import Image
from fastapi.testclient import TestClient


def create_jpeg_bytes() -> bytes:
    """Helper creating simple test JPEG bytes."""
    img = Image.new("RGB", (120, 120), color=(40, 170, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_get_vision_status_endpoint(client: TestClient):
    """Verifies /api/v1/vision/status reports runtime readiness and supported classes."""
    response = client.get("/api/v1/vision/status")
    assert response.status_code == 200
    data = response.json()
    assert "has_active_model" in data
    assert "supported_classes" in data
    assert len(data["supported_classes"]) >= 4
    assert "pipeline_stage" in data


def test_diagnose_leaf_image_endpoint_valid_image(client: TestClient):
    """Verifies /api/v1/vision/diagnose accepts leaf photo and returns severity & model status."""
    img_bytes = create_jpeg_bytes()
    files = {"file": ("test_leaf.jpg", img_bytes, "image/jpeg")}

    response = client.post("/api/v1/vision/diagnose", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "diagnosis_available" in data
    assert "severity_estimation" in data
    assert "image_metadata" in data

    sev = data["severity_estimation"]
    assert "lesion_to_leaf_ratio" in sev
    assert "severity_tier" in sev
    assert "severity_factor_Fv" in sev
    assert "estimation_disclaimer" in sev


def test_diagnose_leaf_image_invalid_empty_file(client: TestClient):
    """Verifies that an empty file upload returns HTTP 400."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/v1/vision/diagnose", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_diagnose_leaf_image_corrupt_file(client: TestClient):
    """Verifies that a corrupt file upload returns HTTP 400."""
    files = {"file": ("corrupt.jpg", b"NOT_VALID_IMAGE_DATA_XYZ", "image/jpeg")}
    response = client.post("/api/v1/vision/diagnose", files=files)
    assert response.status_code == 400
