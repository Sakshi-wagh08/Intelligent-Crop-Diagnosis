import os
from typing import Dict, Any, Optional, Union
from PIL import Image

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.vision.preprocessing import ImagePreprocessor
from backend.app.vision.model import DEFAULT_SUPPORTED_CLASSES
from backend.app.vision.classifier import DiseaseClassifier
from backend.app.vision.segmentation import DiseaseSeverityEstimator
from backend.app.vision.onnx_engine import ONNXDiseaseClassifier
from backend.app.vision.exceptions import ModelWeightsNotFoundError, VisionError


class VisionService:
    """Coordinating service managing preprocessing, classification, and severity estimation."""

    def __init__(
        self,
        pytorch_weights_path: Optional[str] = None,
        onnx_weights_path: Optional[str] = None
    ):
        self.preprocessor = ImagePreprocessor()
        self.severity_estimator = DiseaseSeverityEstimator()

        self.pytorch_weights_path = pytorch_weights_path or getattr(
            settings, "EFFICIENTNET_WEIGHTS_PATH", "ml_models/weights/efficientnet_b0_best.pth"
        )
        self.onnx_weights_path = onnx_weights_path or getattr(
            settings, "EFFICIENTNET_ONNX_PATH", "ml_models/weights/efficientnet_b0_fp16.onnx"
        )

        self.pytorch_classifier: Optional[DiseaseClassifier] = None
        self.onnx_classifier: Optional[ONNXDiseaseClassifier] = None

        self._initialize_classifiers()

    def _initialize_classifiers(self) -> None:
        """Attempts to load trained weights if present on disk."""
        # 1. Try ONNX runtime first (fastest)
        onnx_candidates = [
            self.onnx_weights_path,
            "ml_models/weights/efficientnet_b0.onnx",
            "ml_models/weights/efficientnet_b0_fp16.onnx",
        ]
        # Resolve canonical classes from checkpoint or default supported classes
        active_classes = list(DEFAULT_SUPPORTED_CLASSES)
        if os.path.exists(self.pytorch_weights_path):
            try:
                import torch
                ckpt = torch.load(self.pytorch_weights_path, map_location="cpu")
                if isinstance(ckpt, dict) and "classes" in ckpt:
                    active_classes = ckpt["classes"]
            except Exception:
                pass

        for candidate in onnx_candidates:
            if candidate and os.path.exists(candidate):
                try:
                    self.onnx_classifier = ONNXDiseaseClassifier(
                        onnx_model_path=candidate,
                        classes=active_classes
                    )
                    self.onnx_weights_path = candidate
                    logger.info(f"Loaded ONNX model from: {candidate}")
                    break
                except Exception as e:
                    logger.warning(f"Could not initialize ONNX session from {candidate}: {e}")

        # 2. Try PyTorch checkpoint
        if os.path.exists(self.pytorch_weights_path):
            try:
                self.pytorch_classifier = DiseaseClassifier(checkpoint_path=self.pytorch_weights_path)
                logger.info(f"Loaded PyTorch checkpoint from: {self.pytorch_weights_path}")
            except Exception as e:
                logger.warning(f"Could not load PyTorch checkpoint from {self.pytorch_weights_path}: {e}")

    def reload_weights(self) -> bool:
        """Reloads weights from disk. Returns True if an active model is loaded."""
        self._initialize_classifiers()
        return self.has_active_model

    @property
    def has_active_model(self) -> bool:
        """Returns True if either ONNX or PyTorch classifier is loaded with trained weights."""
        return (
            (self.onnx_classifier is not None and self.onnx_classifier.is_loaded) or
            (self.pytorch_classifier is not None and self.pytorch_classifier.is_loaded)
        )

    def diagnose_image(
        self,
        image_bytes: bytes,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Executes end-to-end vision stream: validation, preprocessing, classification, and severity.

        Args:
            image_bytes: Raw uploaded image file bytes.
            top_k: Number of ranked diagnostic predictions.

        Returns:
            Dictionary containing:
                - diagnosis: Classifier predictions and confidence
                - severity: Lesion-to-leaf ratio S_severity and severity tier
                - image_metadata: Width, height, format
                - model_status: Active runtime details
        """
        # Step 1: Preprocess and validate image
        pil_image = self.preprocessor.validate_and_load(image_bytes)
        width, height = pil_image.size

        # Step 2: Estimate severity (OpenCV heuristic segmentation)
        severity_result = self.severity_estimator.estimate_severity(pil_image)

        # Step 3: Classify pathology
        if not self.has_active_model:
            return {
                "diagnosis_available": False,
                "status": "weights_unavailable",
                "message": (
                    "Model weights not loaded on server. The training pipeline is configured, "
                    "but no validated .pth or .onnx weights file was found in ml_models/weights/."
                ),
                "severity_estimation": severity_result,
                "image_metadata": {
                    "width": width,
                    "height": height,
                    "mode": pil_image.mode,
                    "format": pil_image.format or "JPEG"
                }
            }

        # Run inference via ONNX if available, else PyTorch
        if self.onnx_classifier and self.onnx_classifier.is_loaded:
            tensor_np = self.preprocessor.preprocess_for_onnx(pil_image)
            diagnosis = self.onnx_classifier.predict(tensor_np, top_k=top_k)
        elif self.pytorch_classifier and self.pytorch_classifier.is_loaded:
            tensor_pt = self.preprocessor.preprocess_for_pytorch(pil_image)
            diagnosis = self.pytorch_classifier.predict(tensor_pt, top_k=top_k)
        else:
            raise ModelWeightsNotFoundError("No active classifier is available.")

        return {
            "diagnosis_available": True,
            "status": "success",
            "diagnosis": diagnosis,
            "severity_estimation": severity_result,
            "image_metadata": {
                "width": width,
                "height": height,
                "mode": pil_image.mode,
                "format": pil_image.format or "JPEG"
            }
        }


# Singleton service instance
vision_service = VisionService()
