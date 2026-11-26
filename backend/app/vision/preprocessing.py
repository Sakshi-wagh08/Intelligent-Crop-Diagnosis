import io
from typing import Tuple, Union, Optional
import numpy as np
from PIL import Image, ImageOps
import torch
from torchvision import transforms

from backend.app.vision.exceptions import (
    InvalidImageError,
    ImageTooLargeError,
    CorruptImageError,
)

# Standard EfficientNet-B0 input specifications
EFFICIENTNET_INPUT_SIZE: Tuple[int, int] = (224, 224)
IMAGENET_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)

MAX_IMAGE_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
SUPPORTED_IMAGE_FORMATS: Tuple[str, ...] = ("JPEG", "JPG", "PNG", "WEBP")


def get_efficientnet_transforms(
    input_size: Tuple[int, int] = EFFICIENTNET_INPUT_SIZE
) -> transforms.Compose:
    """Returns standardized PyTorch torchvision transforms for EfficientNet-B0 inference."""
    return transforms.Compose([
        transforms.Resize(input_size, interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


class ImagePreprocessor:
    """Modular image validation, orientation correction, and normalization pipeline."""

    def __init__(
        self,
        input_size: Tuple[int, int] = EFFICIENTNET_INPUT_SIZE,
        max_bytes: int = MAX_IMAGE_FILE_SIZE_BYTES
    ):
        self.input_size = input_size
        self.max_bytes = max_bytes
        self.transform = get_efficientnet_transforms(input_size=self.input_size)

    def validate_and_load(
        self,
        image_input: Union[bytes, io.BytesIO, str]
    ) -> Image.Image:
        """Validates payload constraints and decodes into a PIL Image.

        Args:
            image_input: Raw image bytes, in-memory buffer, or file path.

        Returns:
            Decoded, orientation-corrected RGB PIL Image.

        Raises:
            InvalidImageError: If payload is empty, invalid format, or unsupported type.
            ImageTooLargeError: If payload exceeds max byte limit.
            CorruptImageError: If image headers or bytes cannot be decoded.
        """
        if isinstance(image_input, bytes):
            if len(image_input) == 0:
                raise InvalidImageError("Uploaded image payload is empty (0 bytes).")
            if len(image_input) > self.max_bytes:
                raise ImageTooLargeError(
                    f"Image size ({len(image_input)} bytes) exceeds maximum limit ({self.max_bytes} bytes)."
                )
            stream = io.BytesIO(image_input)
        elif isinstance(image_input, io.BytesIO):
            stream = image_input
            stream.seek(0, io.SEEK_END)
            size = stream.tell()
            stream.seek(0)
            if size == 0:
                raise InvalidImageError("Image stream is empty (0 bytes).")
            if size > self.max_bytes:
                raise ImageTooLargeError(
                    f"Image size ({size} bytes) exceeds maximum limit ({self.max_bytes} bytes)."
                )
        elif isinstance(image_input, str):
            try:
                with open(image_input, "rb") as f:
                    content = f.read()
                return self.validate_and_load(content)
            except FileNotFoundError:
                raise InvalidImageError(f"Image file not found at path: {image_input}")
            except Exception as exc:
                raise CorruptImageError(f"Error opening image file: {exc}")
        else:
            raise InvalidImageError(
                f"Unsupported input type '{type(image_input)}'. Expected bytes, BytesIO, or file path."
            )

        try:
            pil_image = Image.open(stream)
            image_format = (pil_image.format or "").upper()
            if image_format not in SUPPORTED_IMAGE_FORMATS and image_format != "MPO":
                raise InvalidImageError(
                    f"Unsupported image format '{image_format}'. Supported formats: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
                )

            # Verify integrity
            pil_image.verify()

            # Reopen stream because verify() closes/advances stream pointer
            stream.seek(0)
            pil_image = Image.open(stream)

            # Correct orientation from EXIF metadata (mobile phone photo orientation tag)
            pil_image = ImageOps.exif_transpose(pil_image)

            # Ensure image is in 3-channel RGB mode
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Check dimensions are valid non-zero
            width, height = pil_image.size
            if width <= 0 or height <= 0:
                raise CorruptImageError(f"Invalid image dimensions: {width}x{height}")

            return pil_image
        except (InvalidImageError, ImageTooLargeError):
            raise
        except Exception as exc:
            raise CorruptImageError(f"Failed to decode image payload: {exc}")

    def preprocess_for_pytorch(self, pil_image: Image.Image) -> torch.Tensor:
        """Converts PIL RGB image to a normalized PyTorch tensor of shape (1, 3, H, W)."""
        tensor: torch.Tensor = self.transform(pil_image)
        # Add batch dimension: (3, H, W) -> (1, 3, H, W)
        return tensor.unsqueeze(0)

    def preprocess_for_onnx(self, pil_image: Image.Image) -> np.ndarray:
        """Converts PIL RGB image to a normalized NumPy float32 array of shape (1, 3, H, W)."""
        tensor = self.preprocess_for_pytorch(pil_image)
        return tensor.cpu().numpy().astype(np.float32)

    def to_cv2_bgr(self, pil_image: Image.Image) -> np.ndarray:
        """Converts PIL RGB image to OpenCV BGR uint8 array for computer vision segmentation."""
        rgb_array = np.array(pil_image)
        # Convert RGB to BGR
        return rgb_array[:, :, ::-1].copy()
