from typing import Dict, Any, Tuple, Optional, Union
import numpy as np
import cv2
from PIL import Image

from backend.app.vision.exceptions import SeverityEstimationError

# Severity threshold boundaries based on agronomic package-of-practices guidelines
SEVERITY_TIER_LOW_MAX: float = 0.10      # < 10% affected area
SEVERITY_TIER_MODERATE_MAX: float = 0.25 # 10% - 25% affected area
# > 25% affected area is classified as High


class DiseaseSeverityEstimator:
    """Computer vision pipeline for lesion-to-leaf area ratio (S_severity) estimation.

    NOTE ON AGRONOMIC VALIDATION:
    This module computes an image-based heuristic estimate of disease severity. Color-space
    segmentation under variable field illumination, complex backgrounds, and overlapping
    canopies has inherent limitations. Results are explicitly flagged with reliability indicators.
    """

    def __init__(
        self,
        min_leaf_area_pixels: int = 500,
        low_max: float = SEVERITY_TIER_LOW_MAX,
        moderate_max: float = SEVERITY_TIER_MODERATE_MAX
    ):
        self.min_leaf_area_pixels = min_leaf_area_pixels
        self.low_max = low_max
        self.moderate_max = moderate_max

    def estimate_severity(
        self,
        image_input: Union[np.ndarray, Image.Image]
    ) -> Dict[str, Any]:
        """Segments the leaf blade and necrotic/chlorotic lesions to estimate infection severity.

        Args:
            image_input: OpenCV BGR image (np.ndarray) or PIL Image.

        Returns:
            Dictionary containing:
                - lesion_to_leaf_ratio: Float [0.0 - 1.0] (S_severity)
                - severity_tier: 'Low', 'Moderate', or 'High' (or 'None' if uninfected)
                - severity_factor_Fv: Multiplier factor for dosage calculation
                - leaf_pixels: Number of segmented leaf pixels
                - lesion_pixels: Number of segmented lesion pixels
                - leaf_detected: Boolean flag
                - is_reliable: Boolean flag
                - status_message: Informative diagnostic note
                - estimation_disclaimer: Standard heuristic advisory notice
        """
        try:
            if isinstance(image_input, Image.Image):
                rgb_array = np.array(image_input)
                bgr_image = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
            elif isinstance(image_input, np.ndarray):
                bgr_image = image_input.copy()
            else:
                raise SeverityEstimationError(
                    f"Unsupported image input type '{type(image_input)}'. Expected np.ndarray or PIL Image."
                )

            h, w = bgr_image.shape[:2]
            total_image_pixels = h * w

            # 1. Color space conversion to HSV and LAB
            hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)

            # 2. Segment entire leaf canopy (healthy green + diseased tissue)
            # Healthy foliage range in HSV
            green_mask1 = cv2.inRange(hsv, np.array([25, 30, 30]), np.array([90, 255, 255]))
            # Chlorotic yellow foliage range
            yellow_mask = cv2.inRange(hsv, np.array([15, 40, 50]), np.array([35, 255, 255]))
            # Necrotic brown/dark foliage range
            brown_mask = cv2.inRange(hsv, np.array([5, 30, 20]), np.array([25, 255, 180]))

            # Combined leaf mask (vegetation)
            raw_leaf_mask = cv2.bitwise_or(green_mask1, cv2.bitwise_or(yellow_mask, brown_mask))

            # Morphological cleaning to fill small holes and remove speckle noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            leaf_mask = cv2.morphologyEx(raw_leaf_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel, iterations=1)

            leaf_pixels = int(cv2.countNonZero(leaf_mask))

            # Validate leaf presence
            if leaf_pixels < self.min_leaf_area_pixels:
                return {
                    "lesion_to_leaf_ratio": 0.0,
                    "severity_tier": "Undetected",
                    "severity_factor_Fv": 1.0,
                    "leaf_pixels": leaf_pixels,
                    "lesion_pixels": 0,
                    "leaf_detected": False,
                    "is_reliable": False,
                    "status_message": (
                        "Foliage area insufficient or not clearly discernible. "
                        f"Detected {leaf_pixels} leaf pixels (minimum threshold: {self.min_leaf_area_pixels})."
                    ),
                    "estimation_disclaimer": (
                        "Image-based severity estimation requires clear foliage against a neutral background. "
                        "Field lighting and non-foliar elements can impair segmentation accuracy."
                    )
                }

            # 3. Segment necrotic and chlorotic lesions strictly inside the leaf mask
            # Necrotic lesions: dark brown / black spots (e.g. Alternaria target rings, Phytophthora lesions)
            necrotic_hsv_mask = cv2.inRange(hsv, np.array([0, 40, 20]), np.array([22, 255, 160]))
            # High-intensity dark spots using LAB lightness channel L < 80 within leaf
            l_channel = lab[:, :, 0]
            dark_spot_mask = cv2.inRange(l_channel, 10, 85)

            combined_lesion_raw = cv2.bitwise_or(necrotic_hsv_mask, dark_spot_mask)
            # Constrain lesions strictly within the segmented leaf boundary
            lesion_mask = cv2.bitwise_and(combined_lesion_raw, combined_lesion_raw, mask=leaf_mask)

            # Clean lesion mask
            lesion_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_OPEN, lesion_kernel)

            lesion_pixels = int(cv2.countNonZero(lesion_mask))

            # 4. Calculate S_severity = lesion_pixels / leaf_pixels
            ratio = float(lesion_pixels / leaf_pixels)
            # Bound ratio mathematically to [0.0, 1.0]
            ratio = min(max(ratio, 0.0), 1.0)

            # 5. Classify into agronomic severity tiers
            if ratio < 0.01:
                tier = "None / Trace"
            elif ratio <= self.low_max:
                tier = "Low"
            elif ratio <= self.moderate_max:
                tier = "Moderate"
            else:
                tier = "High"

            # Regulatory Agronomic Safety Mandate:
            # Visual foliar severity (S_severity) is strictly distinguished from chemical pesticide dosage calculation.
            # Statutory CIBRC and international label regulations prohibit scaling active ingredient dosages
            # based on foliar symptom severity. Consequently, dosage multiplier Fv is strictly maintained at neutral (1.00).
            fv = 1.00

            # Assess segmentation reliability
            leaf_coverage_ratio = leaf_pixels / total_image_pixels
            is_reliable = (leaf_coverage_ratio >= 0.05) and (leaf_pixels >= self.min_leaf_area_pixels)

            return {
                "lesion_to_leaf_ratio": round(ratio, 4),
                "severity_tier": tier,
                "severity_factor_Fv": fv,
                "leaf_pixels": leaf_pixels,
                "lesion_pixels": lesion_pixels,
                "leaf_coverage_percent": round(leaf_coverage_ratio * 100, 2),
                "leaf_detected": True,
                "is_reliable": is_reliable,
                "status_message": (
                    f"Successfully segmented leaf area and computed {tier} severity ({ratio:.1%}). "
                    "Visual foliar symptom severity does not scale chemical pesticide active ingredient dosage (neutral Fv = 1.00 applied)."
                ),
                "estimation_disclaimer": (
                    "Heuristic OpenCV lesion-to-leaf area estimate (S_severity). "
                    "Visual foliar severity is strictly distinguished from chemical dosage calculations: "
                    "statutory pesticide label rates require neutral Fv = 1.00 to prevent illegal chemical overdosing."
                )
            }

        except Exception as exc:
            raise SeverityEstimationError(f"Disease severity segmentation failed: {exc}")
