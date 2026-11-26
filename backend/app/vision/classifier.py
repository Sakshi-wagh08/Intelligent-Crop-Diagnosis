from typing import List, Dict, Any, Optional, Union
import torch
import torch.nn.functional as F
from PIL import Image

from backend.app.vision.model import load_model_checkpoint, DEFAULT_SUPPORTED_CLASSES
from backend.app.vision.preprocessing import ImagePreprocessor
from backend.app.vision.exceptions import ModelWeightsNotFoundError, InferenceError


class DiseaseClassifier:
    """Inference engine for crop disease diagnosis using PyTorch EfficientNet-B0."""

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        classes: Optional[List[str]] = None,
        device: Optional[str] = None,
        confidence_threshold: float = 0.40
    ):
        self.checkpoint_path = checkpoint_path
        self.classes = classes or DEFAULT_SUPPORTED_CLASSES
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.idx_to_class = {i: c for c, i in self.class_to_idx.items()}
        self.confidence_threshold = confidence_threshold

        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model: Optional[torch.nn.Module] = None
        self.preprocessor = ImagePreprocessor()

        if self.checkpoint_path:
            self.load_weights(self.checkpoint_path)

    @property
    def is_loaded(self) -> bool:
        """Returns True if model weights are loaded and ready for inference."""
        return self.model is not None

    def load_weights(self, checkpoint_path: str) -> None:
        """Loads weights from checkpoint file into model."""
        self.checkpoint_path = checkpoint_path
        model, classes, class_to_idx = load_model_checkpoint(
            checkpoint_path=self.checkpoint_path,
            device=self.device,
            classes=self.classes
        )
        self.model = model
        self.classes = classes
        self.class_to_idx = class_to_idx
        self.idx_to_class = {i: c for c, i in self.class_to_idx.items()}

    def predict(
        self,
        image_input: Union[Image.Image, bytes, torch.Tensor],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Runs forward classification on a plant image.

        Args:
            image_input: PIL Image, raw image bytes, or preprocessed PyTorch Tensor.
            top_k: Number of ranked predictions to return.

        Returns:
            Dictionary with prediction summary:
                - predicted_class: Full class name (e.g. 'Tomato___Early_Blight')
                - crop: Extracted crop name (e.g. 'Tomato')
                - disease: Extracted pathology name (e.g. 'Early Blight')
                - confidence: Softmax probability of top class [0.0 - 1.0]
                - is_confident: Boolean flag indicating if confidence >= threshold
                - top_k_predictions: List of {class_name, confidence}
                - is_unsupported_or_uncertain: Boolean flag

        Raises:
            ModelWeightsNotFoundError: If inference is called before loading weights.
            InferenceError: If an error occurs during model execution.
        """
        if not self.is_loaded or self.model is None:
            raise ModelWeightsNotFoundError(
                "DiseaseClassifier weights are not loaded. Inference cannot proceed without valid model weights."
            )

        # Preprocess input if needed
        if isinstance(image_input, torch.Tensor):
            tensor = image_input.to(self.device)
        elif isinstance(image_input, Image.Image):
            tensor = self.preprocessor.preprocess_for_pytorch(image_input).to(self.device)
        else:
            pil_img = self.preprocessor.validate_and_load(image_input)
            tensor = self.preprocessor.preprocess_for_pytorch(pil_img).to(self.device)

        try:
            with torch.no_grad():
                logits = self.model(tensor)
                probabilities = F.softmax(logits, dim=1).squeeze(0)

            top_probs, top_indices = torch.topk(probabilities, k=min(top_k, len(self.classes)))

            top_predictions = []
            for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
                class_label = self.idx_to_class.get(idx, f"Unknown_Class_{idx}")
                top_predictions.append({
                    "class_name": class_label,
                    "confidence": round(float(prob), 4)
                })

            top_class = top_predictions[0]["class_name"]
            top_conf = top_predictions[0]["confidence"]

            # Parse crop and disease names
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
                "inference_device": str(self.device)
            }
        except Exception as exc:
            raise InferenceError(f"Disease classification forward pass failed: {exc}")
