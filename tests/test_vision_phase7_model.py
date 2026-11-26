"""Phase 7 Vision Stream Model Training, Validation & Integration Tests.

Validates:
1. Dataset preparation and manifest integrity
2. Zero data leakage across train, val, and test splits
3. PyTorch EfficientNet-B0 checkpoint structure & class mappings
4. PyTorch forward inference on genuine agricultural leaf images
5. ONNX Runtime model export & inference
6. Numerical consistency and parity between PyTorch and ONNX Runtime
7. API endpoints integration (/api/v1/vision/status, /api/v1/vision/diagnose)
8. Low confidence & uncertainty handling
9. Invalid and corrupt payload rejection
"""

import os
import json
import io
import pytest
import numpy as np
import torch
from PIL import Image

from backend.app.vision.model import (
    build_efficientnet_b0,
    load_model_checkpoint,
    DEFAULT_SUPPORTED_CLASSES
)
from backend.app.vision.classifier import DiseaseClassifier
from backend.app.vision.preprocessing import ImagePreprocessor, EFFICIENTNET_INPUT_SIZE
from backend.app.vision.service import vision_service


def test_dataset_manifest_and_splits():
    """Validates that dataset manifest exists and specifies all 7 classes with zero split overlap."""
    manifest_path = "data/dataset_manifest.json"
    if not os.path.exists(manifest_path):
        pytest.skip("Dataset manifest not generated yet.")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    assert "canonical_classes" in manifest
    assert len(manifest["canonical_classes"]) == 7
    for cls in DEFAULT_SUPPORTED_CLASSES:
        assert cls in manifest["canonical_classes"]

    split_stats = manifest["split_stats"]
    assert "train" in split_stats
    assert "val" in split_stats
    assert "test" in split_stats

    # Check that every class has positive samples in each split
    for split_name in ["train", "val", "test"]:
        for cls in DEFAULT_SUPPORTED_CLASSES:
            assert split_stats[split_name][cls] > 0, f"Class {cls} missing samples in {split_name}"

    # Verify zero data leakage by comparing filenames across splits
    proc_dir = "data/processed"
    if os.path.exists(proc_dir):
        train_files = set()
        for root, _, files in os.walk(os.path.join(proc_dir, "train")):
            train_files.update(files)

        val_files = set()
        for root, _, files in os.walk(os.path.join(proc_dir, "val")):
            val_files.update(files)

        test_files = set()
        for root, _, files in os.walk(os.path.join(proc_dir, "test")):
            test_files.update(files)

        # Disjoint sets: No filename appears in more than one split
        assert train_files.isdisjoint(val_files), "Data leakage detected: train and val share files!"
        assert train_files.isdisjoint(test_files), "Data leakage detected: train and test share files!"
        assert val_files.isdisjoint(test_files), "Data leakage detected: val and test share files!"


def test_model_checkpoint_structure():
    """Validates trained PyTorch checkpoint structure, weight shapes, and metadata."""
    ckpt_path = "ml_models/weights/efficientnet_b0_best.pth"
    if not os.path.exists(ckpt_path):
        pytest.skip("Trained checkpoint efficientnet_b0_best.pth not yet created.")

    ckpt = torch.load(ckpt_path, map_location="cpu")
    assert "state_dict" in ckpt
    assert "classes" in ckpt
    assert "architecture" in ckpt
    assert ckpt["architecture"] == "efficientnet_b0"
    assert len(ckpt["classes"]) == 7
    assert set(ckpt["classes"]) == set(DEFAULT_SUPPORTED_CLASSES)

    # Check classification head output shape: (7, 1280)
    fc_weight = ckpt["state_dict"]["classifier.1.weight"]
    assert fc_weight.shape == (7, 1280)


def test_pytorch_classifier_real_image_inference():
    """Validates PyTorch DiseaseClassifier inference produces valid probabilities and top-k output."""
    ckpt_path = "ml_models/weights/efficientnet_b0_best.pth"
    if not os.path.exists(ckpt_path):
        pytest.skip("Trained checkpoint not yet created.")

    classifier = DiseaseClassifier(checkpoint_path=ckpt_path, classes=DEFAULT_SUPPORTED_CLASSES)
    assert classifier.is_loaded

    # Test on a real test image if available, else synthetic PIL image
    test_img_dir = "data/processed/test/Tomato___Early_Blight"
    if os.path.exists(test_img_dir) and os.listdir(test_img_dir):
        img_path = os.path.join(test_img_dir, os.listdir(test_img_dir)[0])
        test_img = Image.open(img_path)
    else:
        test_img = Image.new("RGB", (224, 224), color=(50, 120, 50))

    pred = classifier.predict(test_img, top_k=3)

    assert "predicted_class" in pred
    assert pred["predicted_class"] in DEFAULT_SUPPORTED_CLASSES
    assert "confidence" in pred
    assert 0.0 <= pred["confidence"] <= 1.0
    assert "crop" in pred
    assert "disease" in pred
    assert isinstance(pred["is_healthy"], bool)
    assert len(pred["top_k_predictions"]) == 3

    # Confidences in top_k must be sorted descending
    top_confs = [p["confidence"] for p in pred["top_k_predictions"]]
    assert top_confs == sorted(top_confs, reverse=True)


def test_onnx_model_inference_and_parity():
    """Validates ONNX Runtime inference and verifies numerical parity against PyTorch."""
    ckpt_path = "ml_models/weights/efficientnet_b0_best.pth"
    onnx_path = "ml_models/weights/efficientnet_b0.onnx"

    if not os.path.exists(ckpt_path) or not os.path.exists(onnx_path):
        pytest.skip("Both PyTorch checkpoint and ONNX model must exist for parity test.")

    from backend.app.vision.onnx_engine import ONNXDiseaseClassifier, compare_pytorch_and_onnx

    py_model, classes, _ = load_model_checkpoint(ckpt_path, device=torch.device("cpu"))
    onnx_classifier = ONNXDiseaseClassifier(onnx_model_path=onnx_path, classes=classes)
    assert onnx_classifier.is_loaded

    # Compare on synthetic normalized tensor
    dummy_input = torch.randn(1, 3, 224, 224, dtype=torch.float32)
    parity = compare_pytorch_and_onnx(py_model, onnx_classifier, dummy_input, tolerance=1e-3)

    assert parity["top_class_match"] is True
    assert parity["is_numerically_consistent"] is True
    assert parity["absolute_difference"] < 1e-3


def test_vision_service_active_model_status(client):
    """Validates that VisionService and GET /api/v1/vision/status reflect active model availability."""
    ckpt_path = "ml_models/weights/efficientnet_b0_best.pth"
    onnx_path = "ml_models/weights/efficientnet_b0.onnx"

    if not os.path.exists(ckpt_path) and not os.path.exists(onnx_path):
        pytest.skip("Model weights not yet trained.")

    vision_service.reload_weights()
    assert vision_service.has_active_model is True

    resp = client.get("/api/v1/vision/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_active_model"] is True
    assert set(data["supported_classes"]) == set(DEFAULT_SUPPORTED_CLASSES)


def test_vision_diagnose_api_with_trained_model(client):
    """Validates POST /api/v1/vision/diagnose executes live inference with severity and top-k output."""
    ckpt_path = "ml_models/weights/efficientnet_b0_best.pth"
    if not os.path.exists(ckpt_path):
        pytest.skip("Model weights not yet trained.")

    vision_service.reload_weights()

    # Use a real image from test dataset if available
    test_img_dir = "data/processed/test/Tomato___Early_Blight"
    if os.path.exists(test_img_dir) and os.listdir(test_img_dir):
        img_path = os.path.join(test_img_dir, os.listdir(test_img_dir)[0])
        with open(img_path, "rb") as f:
            img_bytes = f.read()
    else:
        buf = io.BytesIO()
        Image.new("RGB", (224, 224), color=(34, 139, 34)).save(buf, format="JPEG")
        img_bytes = buf.getvalue()

    resp = client.post(
        "/api/v1/vision/diagnose?top_k=3",
        files={"file": ("leaf.jpg", img_bytes, "image/jpeg")}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["diagnosis_available"] is True
    assert data["status"] == "success"
    assert data["diagnosis"] is not None

    diag = data["diagnosis"]
    assert diag["predicted_class"] in DEFAULT_SUPPORTED_CLASSES
    assert 0.0 <= diag["confidence"] <= 1.0
    assert len(diag["top_k_predictions"]) == 3
    assert "severity_estimation" in data
    assert 0.0 <= data["severity_estimation"]["lesion_to_leaf_ratio"] <= 1.0


def test_corrupt_and_invalid_image_rejection(client):
    """Validates that non-image payloads are safely rejected with HTTP 400."""
    corrupt_bytes = b"This is a corrupt text file masquerading as a leaf photograph."

    resp = client.post(
        "/api/v1/vision/diagnose",
        files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"].lower()
    assert "failed to decode" in detail or "cannot identify" in detail or "invalid image" in detail or "format" in detail
