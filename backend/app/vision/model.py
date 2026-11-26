import os
from typing import List, Dict, Optional, Tuple
import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

from backend.app.vision.exceptions import ModelWeightsNotFoundError

# Default supported disease & health classes aligned with database agronomic entities
DEFAULT_SUPPORTED_CLASSES: List[str] = [
    "Potato___Late_Blight",
    "Potato___healthy",
    "Rice___Blast",
    "Rice___healthy",
    "Tomato___Early_Blight",
    "Tomato___Late_Blight",
    "Tomato___healthy",
]


def build_efficientnet_b0(
    num_classes: int = len(DEFAULT_SUPPORTED_CLASSES),
    pretrained_backbone: bool = True,
    dropout_rate: float = 0.2,
    freeze_backbone: bool = False
) -> nn.Module:
    """Builds an EfficientNet-B0 architecture with a custom classification head.

    Args:
        num_classes: Number of target agricultural disease classes.
        pretrained_backbone: Whether to load ImageNet pre-trained weights for feature extraction.
        dropout_rate: Dropout probability in classification head.
        freeze_backbone: If True, freezes feature extractor parameters for linear probe training.

    Returns:
        Configured PyTorch nn.Module.
    """
    weights = EfficientNet_B0_Weights.DEFAULT if pretrained_backbone else None
    model = efficientnet_b0(weights=weights)

    if freeze_backbone:
        for param in model.features.parameters():
            param.requires_grad = False

    # EfficientNet-B0 has 1280 output features before classification head
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=dropout_rate, inplace=True),
        nn.Linear(in_features=in_features, out_features=num_classes)
    )

    return model


def load_model_checkpoint(
    checkpoint_path: str,
    device: Optional[torch.device] = None,
    classes: Optional[List[str]] = None
) -> Tuple[nn.Module, List[str], Dict[str, int]]:
    """Loads a trained EfficientNet-B0 checkpoint from disk.

    Args:
        checkpoint_path: Path to .pth checkpoint file.
        device: Target execution device (CPU or CUDA).
        classes: Optional override list of class names.

    Returns:
        Tuple of (model, class_names, class_to_idx).

    Raises:
        ModelWeightsNotFoundError: If the checkpoint file does not exist on disk.
    """
    if not os.path.exists(checkpoint_path):
        raise ModelWeightsNotFoundError(
            f"Model weights checkpoint not found at: '{checkpoint_path}'. "
            "Please train or download validated model weights before running inference."
        )

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    checkpoint = torch.load(checkpoint_path, map_location=device)

    # Extract metadata from checkpoint if present
    if isinstance(checkpoint, dict) and "classes" in checkpoint:
        class_names = checkpoint["classes"]
        class_to_idx = checkpoint.get("class_to_idx", {c: i for i, c in enumerate(class_names)})
        state_dict = checkpoint["state_dict"]
    elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        class_names = classes or DEFAULT_SUPPORTED_CLASSES
        class_to_idx = {c: i for i, c in enumerate(class_names)}
        state_dict = checkpoint["state_dict"]
    else:
        # Checkpoint is raw state_dict
        class_names = classes or DEFAULT_SUPPORTED_CLASSES
        class_to_idx = {c: i for i, c in enumerate(class_names)}
        state_dict = checkpoint

    model = build_efficientnet_b0(
        num_classes=len(class_names),
        pretrained_backbone=False
    )
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    return model, class_names, class_to_idx
