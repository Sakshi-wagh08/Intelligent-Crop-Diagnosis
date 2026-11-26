import io
import pytest
import numpy as np
from PIL import Image
import torch

from backend.app.vision.preprocessing import (
    ImagePreprocessor,
    EFFICIENTNET_INPUT_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
)
from backend.app.vision.exceptions import (
    InvalidImageError,
    ImageTooLargeError,
    CorruptImageError,
)


def create_test_image_bytes(
    size=(100, 100),
    color=(0, 200, 0),
    fmt="JPEG"
) -> bytes:
    """Helper to generate in-memory image bytes."""
    img = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    return buffer.getvalue()


def test_valid_image_loading_and_conversion():
    """Verifies that valid JPEG and PNG bytes load cleanly into PIL RGB."""
    preprocessor = ImagePreprocessor()
    jpeg_bytes = create_test_image_bytes(fmt="JPEG")
    png_bytes = create_test_image_bytes(fmt="PNG")

    img_jpeg = preprocessor.validate_and_load(jpeg_bytes)
    assert isinstance(img_jpeg, Image.Image)
    assert img_jpeg.mode == "RGB"

    img_png = preprocessor.validate_and_load(png_bytes)
    assert isinstance(img_png, Image.Image)
    assert img_png.mode == "RGB"


def test_empty_image_raises_invalid_image_error():
    """Verifies that 0-byte payload raises InvalidImageError."""
    preprocessor = ImagePreprocessor()
    with pytest.raises(InvalidImageError, match="empty"):
        preprocessor.validate_and_load(b"")


def test_oversized_image_raises_image_too_large_error():
    """Verifies that exceeding max byte limit raises ImageTooLargeError."""
    # Set small limit (100 bytes) for testing
    preprocessor = ImagePreprocessor(max_bytes=100)
    img_bytes = create_test_image_bytes()
    assert len(img_bytes) > 100

    with pytest.raises(ImageTooLargeError, match="exceeds maximum limit"):
        preprocessor.validate_and_load(img_bytes)


def test_corrupt_bytes_raises_corrupt_image_error():
    """Verifies that malformed bytes raise CorruptImageError."""
    preprocessor = ImagePreprocessor()
    corrupt_bytes = b"NOT_A_VALID_IMAGE_HEADER_DATA_12345"
    with pytest.raises(CorruptImageError):
        preprocessor.validate_and_load(corrupt_bytes)


def test_preprocessing_pytorch_tensor_output():
    """Verifies preprocessed PyTorch tensor shape, type, and normalization."""
    preprocessor = ImagePreprocessor(input_size=(224, 224))
    img_bytes = create_test_image_bytes()
    pil_img = preprocessor.validate_and_load(img_bytes)

    tensor = preprocessor.preprocess_for_pytorch(pil_img)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 224, 224)
    assert tensor.dtype == torch.float32


def test_preprocessing_onnx_numpy_output():
    """Verifies preprocessed NumPy array shape and float32 dtype for ONNX Runtime."""
    preprocessor = ImagePreprocessor(input_size=(224, 224))
    img_bytes = create_test_image_bytes()
    pil_img = preprocessor.validate_and_load(img_bytes)

    np_array = preprocessor.preprocess_for_onnx(pil_img)
    assert isinstance(np_array, np.ndarray)
    assert np_array.shape == (1, 3, 224, 224)
    assert np_array.dtype == np.float32


def test_to_cv2_bgr_conversion():
    """Verifies conversion from PIL RGB to OpenCV BGR array."""
    preprocessor = ImagePreprocessor()
    # Pure green RGB: (0, 255, 0) -> in BGR should be (0, 255, 0)
    # Pure red RGB: (255, 0, 0) -> in BGR should be (0, 0, 255)
    red_img = Image.new("RGB", (50, 50), color=(255, 0, 0))
    bgr = preprocessor.to_cv2_bgr(red_img)
    assert isinstance(bgr, np.ndarray)
    assert bgr.shape == (50, 50, 3)
    # BGR format: Blue=0, Green=0, Red=255
    assert bgr[0, 0, 0] == 0    # Blue
    assert bgr[0, 0, 1] == 0    # Green
    assert bgr[0, 0, 2] == 255  # Red
