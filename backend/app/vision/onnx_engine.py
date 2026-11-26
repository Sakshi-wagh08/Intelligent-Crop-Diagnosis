import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import onnxruntime as ort

from backend.app.vision.model import DEFAULT_SUPPORTED_CLASSES
from backend.app.vision.preprocessing import ImagePreprocessor
from backend.app.vision.exceptions import ModelWeightsNotFoundError, InferenceError


def export_pytorch_to_onnx(
    model: nn.Module,
    output_onnx_path: str,
    input_size: Tuple[int, int] = (224, 224),
    opset_version: int = 17,
    dynamic_batch: bool = True
) -> str:
    """Exports a trained PyTorch EfficientNet-B0 model to ONNX format.

    Args:
        model: PyTorch nn.Module in eval mode.
        output_onnx_path: Destination path on disk for .onnx artifact.
        input_size: Input spatial dimensions (H, W).
        opset_version: Target ONNX operator set version (default 17).
        dynamic_batch: Whether to allow variable batch sizes at inference time.

    Returns:
        Absolute path to exported ONNX file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_onnx_path)), exist_ok=True)
    model.eval()

    dummy_input = torch.randn(1, 3, input_size[0], input_size[1], dtype=torch.float32)

    dynamic_axes = {"input": {0: "batch_size"}, "output": {0: "batch_size"}} if dynamic_batch else None

    torch.onnx.export(
        model,
        dummy_input,
        output_onnx_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes=dynamic_axes
    )

    return os.path.abspath(output_onnx_path)


class ONNXDiseaseClassifier:
    """High-performance edge inference engine using ONNX Runtime."""

    def __init__(
        self,
        onnx_model_path: Optional[str] = None,
        classes: Optional[List[str]] = None,
        confidence_threshold: float = 0.40
    ):
        self.onnx_model_path = onnx_model_path
        self.classes = classes or DEFAULT_SUPPORTED_CLASSES
        self.idx_to_class = {i: c for i, c in enumerate(self.classes)}
        self.confidence_threshold = confidence_threshold

        self.session: Optional[ort.InferenceSession] = None
        self.input_name: Optional[str] = None
        self.output_name: Optional[str] = None
        self.preprocessor = ImagePreprocessor()

        if self.onnx_model_path:
            self.load_model(self.onnx_model_path)

    @property
    def is_loaded(self) -> bool:
        """Returns True if an ONNX session is active."""
        return self.session is not None

    def load_model(self, onnx_model_path: str) -> None:
        """Initializes ONNX Runtime InferenceSession with available execution providers."""
        if not os.path.exists(onnx_model_path):
            raise ModelWeightsNotFoundError(
                f"ONNX model file not found at: '{onnx_model_path}'. "
                "Export or train model before initializing ONNX session."
            )

        self.onnx_model_path = onnx_model_path
        # Use CPUExecutionProvider by default (CUDAExecutionProvider if available)
        providers = ["CPUExecutionProvider"]
        if "CUDAExecutionProvider" in ort.get_available_providers():
            providers.insert(0, "CUDAExecutionProvider")

        self.session = ort.InferenceSession(self.onnx_model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def predict(
        self,
        numpy_input: np.ndarray,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Executes forward inference using ONNX Runtime.

        Args:
            numpy_input: Preprocessed float32 array of shape (1, 3, 224, 224).
            top_k: Number of ranked predictions to return.

        Returns:
            Dictionary with prediction results and softmax probabilities.
        """
        if not self.is_loaded or self.session is None:
            raise ModelWeightsNotFoundError("ONNX InferenceSession is not initialized with model weights.")

        try:
            # Ensure shape is (B, C, H, W) and dtype float32
            if numpy_input.ndim == 3:
                numpy_input = np.expand_dims(numpy_input, axis=0)
            numpy_input = numpy_input.astype(np.float32)

            outputs = self.session.run([self.output_name], {self.input_name: numpy_input})
            logits = outputs[0][0]  # First batch item logits

            # Compute softmax numerically stable
            exp_logits = np.exp(logits - np.max(logits))
            probabilities = exp_logits / np.sum(exp_logits)

            # Top-K
            top_indices = np.argsort(probabilities)[::-1][:min(top_k, len(self.classes))]

            top_predictions = []
            for idx in top_indices:
                class_label = self.idx_to_class.get(int(idx), f"Unknown_{idx}")
                top_predictions.append({
                    "class_name": class_label,
                    "confidence": round(float(probabilities[idx]), 4)
                })

            top_class = top_predictions[0]["class_name"]
            top_conf = top_predictions[0]["confidence"]

            if "___" in top_class:
                crop_part, disease_part = top_class.split("___", 1)
                crop_name = crop_part.replace("_", " ")
                disease_name = disease_part.replace("_", " ")
            else:
                crop_name = "Unknown"
                disease_name = top_class

            is_confident = top_conf >= self.confidence_threshold
            is_healthy = "healthy" in disease_name.lower()

            return {
                "predicted_class": top_class,
                "crop": crop_name,
                "disease": disease_name,
                "is_healthy": is_healthy,
                "confidence": top_conf,
                "is_confident": is_confident,
                "confidence_threshold": self.confidence_threshold,
                "top_k_predictions": top_predictions,
                "is_unsupported_or_uncertain": not is_confident,
                "inference_device": "ONNXRuntime",
                "runtime_backend": "ONNXRuntime",
                "active_providers": self.session.get_providers()
            }
        except Exception as exc:
            raise InferenceError(f"ONNX Runtime inference failed: {exc}")


def compare_pytorch_and_onnx(
    pytorch_model: nn.Module,
    onnx_classifier: ONNXDiseaseClassifier,
    test_tensor: torch.Tensor,
    tolerance: float = 1e-4
) -> Dict[str, Any]:
    """Numerically compares PyTorch model and ONNX Runtime predictions on the exact same tensor."""
    pytorch_model.eval()
    with torch.no_grad():
        pt_logits = pytorch_model(test_tensor).cpu().numpy()[0]
        pt_probs = torch.softmax(torch.from_numpy(pt_logits), dim=0).numpy()

    onnx_input = test_tensor.cpu().numpy().astype(np.float32)
    onnx_pred = onnx_classifier.predict(onnx_input)
    onnx_top_conf = onnx_pred["confidence"]
    pt_top_conf = float(np.max(pt_probs))

    conf_diff = abs(pt_top_conf - onnx_top_conf)
    matches = conf_diff <= tolerance

    return {
        "pytorch_top_confidence": round(pt_top_conf, 4),
        "onnx_top_confidence": round(onnx_top_conf, 4),
        "absolute_difference": float(conf_diff),
        "tolerance": tolerance,
        "is_numerically_consistent": bool(matches),
        "top_class_match": pytorch_model.classifier[1].out_features == len(onnx_classifier.classes)
    }
