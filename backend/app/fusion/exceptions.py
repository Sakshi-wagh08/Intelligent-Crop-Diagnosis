"""Domain exceptions for Multimodal Fusion and Recommendation Engine."""


class FusionError(Exception):
    """Base exception for multimodal fusion operations."""
    pass


class IncompatibleCropDiseaseError(FusionError):
    """Raised when diagnosed disease does not clinically infect the specified crop."""
    def __init__(self, crop: str, disease: str):
        super().__init__(f"Incompatible pathology: '{disease}' is not a documented pathogen of crop '{crop}'.")


class LowDiagnosticConfidenceError(FusionError):
    """Raised when vision diagnostic confidence falls below minimum safety threshold."""
    def __init__(self, confidence: float, threshold: float):
        super().__init__(
            f"Diagnostic confidence ({confidence * 100:.1f}%) is below safety threshold ({threshold * 100:.1f}%). "
            "Chemical recommendation withheld to prevent misapplication."
        )


class PhiViolationError(FusionError):
    """Raised when crop harvest is scheduled before chemical Pre-Harvest Interval (PHI) expires."""
    def __init__(self, days_to_harvest: int, phi_days: int, chemical: str):
        super().__init__(
            f"Pre-Harvest Interval (PHI) violation: chemical '{chemical}' requires a minimum {phi_days} days PHI, "
            f"but harvest is scheduled in {days_to_harvest} days. Application prohibited."
        )


class ChemicalIncompatibilityError(FusionError):
    """Raised when proposed tank-mix chemicals present known phytotoxic incompatibility."""
    def __init__(self, ingredient_a: str, ingredient_b: str, warning: str):
        super().__init__(
            f"Chemical incompatibility between '{ingredient_a}' and '{ingredient_b}': {warning}"
        )


class MissingTreatmentDataError(FusionError):
    """Raised when required base dosage or label maximum is missing from knowledge base."""
    def __init__(self, details: str):
        super().__init__(f"Missing treatment data: {details}")


class UnverifiedRecommendationError(FusionError):
    """Raised when an unverified demonstration record is evaluated without explicit demo override."""
    def __init__(self, details: str):
        super().__init__(f"Unverified agricultural record: {details}")
