import numpy as np
import cv2
from PIL import Image

from backend.app.vision.segmentation import DiseaseSeverityEstimator


def create_synthetic_leaf(
    img_size=(200, 200),
    leaf_radius=60,
    lesion_radius=0
) -> np.ndarray:
    """Creates a synthetic OpenCV BGR leaf with an optional circular necrotic lesion."""
    img = np.zeros((img_size[1], img_size[0], 3), dtype=np.uint8)
    center = (img_size[0] // 2, img_size[1] // 2)

    # Draw healthy green leaf blade: BGR (30, 160, 40)
    cv2.circle(img, center, leaf_radius, (30, 160, 40), -1)

    # Draw dark necrotic lesion if specified
    if lesion_radius > 0:
        # BGR (15, 30, 45) dark brown necrotic tissue
        cv2.circle(img, center, lesion_radius, (15, 30, 45), -1)

    return img


def test_clean_healthy_leaf_severity():
    """Verifies that an uninfected green leaf yields 'None / Trace' severity."""
    estimator = DiseaseSeverityEstimator(min_leaf_area_pixels=100)
    leaf_img = create_synthetic_leaf(lesion_radius=0)

    res = estimator.estimate_severity(leaf_img)
    assert res["leaf_detected"] is True
    assert res["is_reliable"] is True
    assert res["severity_tier"] == "None / Trace"
    assert res["lesion_to_leaf_ratio"] == 0.0
    assert res["severity_factor_Fv"] == 1.0
    assert res["lesion_pixels"] == 0
    assert res["leaf_pixels"] > 5000


def test_moderate_disease_leaf_severity():
    """Verifies that ~13% lesion coverage yields 'Moderate' severity and neutral Fv = 1.00."""
    estimator = DiseaseSeverityEstimator(min_leaf_area_pixels=100)
    # Leaf radius 60 (area ~11310), lesion radius 22 (area ~1520 -> ~13.4%)
    leaf_img = create_synthetic_leaf(leaf_radius=60, lesion_radius=22)

    res = estimator.estimate_severity(leaf_img)
    assert res["leaf_detected"] is True
    assert res["is_reliable"] is True
    assert res["severity_tier"] == "Moderate"
    assert 0.10 <= res["lesion_to_leaf_ratio"] <= 0.25
    assert res["severity_factor_Fv"] == 1.0
    assert res["lesion_pixels"] > 1000


def test_high_disease_leaf_severity():
    """Verifies that >25% lesion coverage yields 'High' severity and neutral Fv = 1.00."""
    estimator = DiseaseSeverityEstimator(min_leaf_area_pixels=100)
    # Leaf radius 60 (area ~11310), lesion radius 35 (area ~3848 -> ~34%)
    leaf_img = create_synthetic_leaf(leaf_radius=60, lesion_radius=35)

    res = estimator.estimate_severity(leaf_img)
    assert res["leaf_detected"] is True
    assert res["severity_tier"] == "High"
    assert res["lesion_to_leaf_ratio"] > 0.25
    assert res["severity_factor_Fv"] == 1.0


def test_non_foliar_image_undetected():
    """Verifies that an image without foliar vegetation reports 'Undetected' and is_reliable=False."""
    estimator = DiseaseSeverityEstimator(min_leaf_area_pixels=500)
    # Blank solid white background (e.g. tabletop or document)
    blank_img = np.full((200, 200, 3), 255, dtype=np.uint8)

    res = estimator.estimate_severity(blank_img)
    assert res["leaf_detected"] is False
    assert res["is_reliable"] is False
    assert res["severity_tier"] == "Undetected"
    assert res["lesion_to_leaf_ratio"] == 0.0
    assert res["severity_factor_Fv"] == 1.0
    assert "insufficient" in res["status_message"].lower()


def test_pil_image_input_compatibility():
    """Verifies that PIL Image input is accepted and produces identical results to np.ndarray."""
    estimator = DiseaseSeverityEstimator(min_leaf_area_pixels=100)
    leaf_bgr = create_synthetic_leaf(leaf_radius=60, lesion_radius=22)
    leaf_rgb = cv2.cvtColor(leaf_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(leaf_rgb)

    res = estimator.estimate_severity(pil_img)
    assert res["leaf_detected"] is True
    assert res["severity_tier"] == "Moderate"
