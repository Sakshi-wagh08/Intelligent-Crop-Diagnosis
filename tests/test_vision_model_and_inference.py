import os
import tempfile
import pytest
import torch
import torch.nn as nn
from PIL import Image

from backend.app.vision.model import (
    build_efficientnet_b0,
    load_model_checkpoint,
    DEFAULT_SUPPORTED_CLASSES,
)
from backend.app.vision.classifier import DiseaseClassifier
from backend.app.vision.exceptions import ModelWeightsNotFoundError


def test_build_efficientnet_b0_architecture():
    """Verifies that the EfficientNet-B0 transfer learning architecture builds with correct head dimensions."""
    classes = ["Tomato___Early_Blight", "Tomato___Late_Blight", "Tomato___healthy"]
    model = build_efficientnet_b0(num_classes=len(classes), pretrained_backbone=False)

    assert isinstance(model, nn.Module)
    # Check classifier structure: Dropout + Linear
    assert len(model.classifier) == 2
    assert isinstance(model.classifier[1], nn.Linear)
    assert model.classifier[1].in_features == 1280
    assert model.classifier[1].out_features == len(classes)

    # Test forward pass with dummy tensor
    dummy_input = torch.randn(2, 3, 224, 224)
    output = model(dummy_input)
    assert output.shape == (2, len(classes))


def test_load_model_checkpoint_missing_raises_error():
    """Verifies that attempting to load nonexistent checkpoint raises ModelWeightsNotFoundError."""
    nonexistent_path = "ml_models/weights/nonexistent_model_checkpoint_12345.pth"
    with pytest.raises(ModelWeightsNotFoundError, match="Model weights checkpoint not found"):
        load_model_checkpoint(nonexistent_path)


def test_disease_classifier_unloaded_predict_raises_error():
    """Verifies that DiseaseClassifier refuses inference when model weights are not loaded."""
    classifier = DiseaseClassifier(checkpoint_path=None)
    assert not classifier.is_loaded

    test_img = Image.new("RGB", (224, 224), color=(0, 200, 0))
    with pytest.raises(ModelWeightsNotFoundError, match="DiseaseClassifier weights are not loaded"):
        classifier.predict(test_img)


def test_disease_classifier_inference_with_trained_checkpoint():
    """Verifies complete forward prediction and output dictionary structure using a valid checkpoint."""
    classes = ["Tomato___Early_Blight", "Tomato___Late_Blight", "Potato___Late_Blight", "Rice___Blast"]
    model = build_efficientnet_b0(num_classes=len(classes), pretrained_backbone=False)

    with tempfile.TemporaryDirectory() as tmp_dir:
        ckpt_path = os.path.join(tmp_dir, "test_checkpoint.pth")
        torch.save({
            "state_dict": model.state_dict(),
            "classes": classes,
            "class_to_idx": {c: i for i, c in enumerate(classes)},
            "architecture": "efficientnet_b0"
        }, ckpt_path)

        classifier = DiseaseClassifier(checkpoint_path=ckpt_path, classes=classes)
        assert classifier.is_loaded

        # Run inference on synthetic image
        test_img = Image.new("RGB", (224, 224), color=(30, 180, 40))
        result = classifier.predict(test_img, top_k=3)

        assert "predicted_class" in result
        assert "crop" in result
        assert "disease" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
        assert "top_k_predictions" in result
        assert len(result["top_k_predictions"]) == 3
        assert result["predicted_class"] in classes
        assert result["crop"] in ["Tomato", "Potato", "Rice"]
