"""Vision Stream Exception Hierarchy."""


class VisionError(Exception):
    """Base exception for all vision stream operations."""
    pass


class InvalidImageError(VisionError):
    """Raised when an uploaded file is not a valid image format or is empty."""
    pass


class ImageTooLargeError(VisionError):
    """Raised when an uploaded image exceeds the maximum permitted file size."""
    pass


class CorruptImageError(VisionError):
    """Raised when an image payload cannot be decoded by image processing libraries."""
    pass


class ModelWeightsNotFoundError(VisionError):
    """Raised when model weights or ONNX artifacts cannot be found on disk."""
    pass


class InferenceError(VisionError):
    """Raised when an error occurs during neural network forward inference."""
    pass


class SeverityEstimationError(VisionError):
    """Raised when computer vision severity segmentation fails."""
    pass
