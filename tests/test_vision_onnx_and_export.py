import os
import tempfile
import pytest
import torch
import numpy as np

from backend.app.vision.model import build_efficientnet_b0
from backend.app.vision.onnx_engine import (
    export_pytorch_to_onnx,
    ONNXDiseaseClassifier,
    compare_pytorch_and_onnx,
)
from backend.app.vision.exceptions import ModelWeightsNotFoundError


def test_export_pytorch_to_onnx_and_inference():
    """Verifies exporting an initialized model to ONNX and running forward inference with ONNX Runtime."""
    classes = ["Tomato___Early_Blight", "Tomato___Late_Blight", "Potato___Late_Blight"]
    model = build_efficientnet_b0(num_classes=len(classes), pretrained_backbone=False)
    model.eval()

    with tempfile.TemporaryDirectory() as tmp_dir:
        onnx_path = os.path.join(tmp_dir, "test_efficientnet.onnx")

        # 1. Export to ONNX
        exported_path = export_pytorch_to_onnx(model, onnx_path, opset_version=17)
        assert os.path.exists(exported_path)
        assert os.path.getsize(exported_path) > 1000

        # 2. Initialize ONNX classifier
        onnx_classifier = ONNXDiseaseClassifier(onnx_model_path=exported_path, classes=classes)
        assert onnx_classifier.is_loaded

        # 3. Run forward inference
        dummy_np = np.random.randn(1, 3, 224, 224).astype(np.float32)
        res = onnx_classifier.predict(dummy_np, top_k=2)

        assert "predicted_class" in res
        assert "confidence" in res
        assert res["runtime_backend"] == "ONNXRuntime"
        assert len(res["top_k_predictions"]) == 2
        assert res["predicted_class"] in classes


def test_compare_pytorch_and_onnx_numerical_consistency():
    """Verifies that PyTorch and ONNX Runtime predictions match within 1e-3 tolerance on identical input."""
    classes = ["Tomato___Early_Blight", "Tomato___Late_Blight"]
    model = build_efficientnet_b0(num_classes=len(classes), pretrained_backbone=False)
    model.eval()

    with tempfile.TemporaryDirectory() as tmp_dir:
        onnx_path = os.path.join(tmp_dir, "test_compare.onnx")
        export_pytorch_to_onnx(model, onnx_path, opset_version=17)

        onnx_classifier = ONNXDiseaseClassifier(onnx_model_path=onnx_path, classes=classes)
        test_tensor = torch.randn(1, 3, 224, 224, dtype=torch.float32)

        comparison = compare_pytorch_and_onnx(
            pytorch_model=model,
            onnx_classifier=onnx_classifier,
            test_tensor=test_tensor,
            tolerance=1e-3
        )

        assert comparison["is_numerically_consistent"] is True
        assert comparison["absolute_difference"] <= 1e-3


def test_onnx_missing_file_raises_error():
    """Verifies that initializing ONNX classifier with missing file raises ModelWeightsNotFoundError."""
    missing_path = "ml_models/weights/nonexistent_model.onnx"
    classifier = ONNXDiseaseClassifier(onnx_model_path=None)
    assert not classifier.is_loaded

    with pytest.raises(ModelWeightsNotFoundError, match="ONNX model file not found"):
        classifier.load_model(missing_path)
