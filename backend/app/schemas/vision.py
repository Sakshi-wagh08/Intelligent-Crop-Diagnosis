from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PredictionItem(BaseModel):
    """Ranked class prediction item."""
    class_name: str = Field(..., description="Full class label, e.g. 'Tomato___Early_Blight'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Softmax confidence probability")


class DiagnosisResult(BaseModel):
    """Disease classification prediction summary."""
    predicted_class: str
    crop: str
    disease: str
    is_healthy: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_confident: bool
    confidence_threshold: float
    top_k_predictions: List[PredictionItem] = []
    is_unsupported_or_uncertain: bool = False
    inference_device: Optional[str] = None


class SeverityResult(BaseModel):
    """Lesion-to-leaf area ratio and heuristic severity estimate."""
    lesion_to_leaf_ratio: float = Field(..., ge=0.0, le=1.0, description="S_severity ratio")
    severity_tier: str = Field(..., description="'None / Trace', 'Low', 'Moderate', 'High', or 'Undetected'")
    severity_factor_Fv: float = Field(
        1.00,
        description="Neutral severity factor (1.00). Statutory pesticide labels strictly prohibit active ingredient dosage multipliers based on foliar symptom severity."
    )
    leaf_pixels: int
    lesion_pixels: int
    leaf_coverage_percent: Optional[float] = None
    leaf_detected: bool
    is_reliable: bool
    status_message: str
    estimation_disclaimer: str


class VisionDiagnosisResponse(BaseModel):
    """Response returned by vision diagnosis endpoint."""
    diagnosis_available: bool
    status: str
    message: Optional[str] = None
    diagnosis: Optional[DiagnosisResult] = None
    severity_estimation: SeverityResult
    image_metadata: Dict[str, Any]


class VisionStatusResponse(BaseModel):
    """Operational status of the vision stream."""
    has_active_model: bool
    pytorch_loaded: bool
    onnx_loaded: bool
    supported_classes: List[str]
    pytorch_weights_path: str
    onnx_weights_path: str
    pipeline_stage: str = Field(
        "Phase 2: Vision Stream - Training pipeline ready; awaiting verified dataset weights.",
        description="Current engineering stage"
    )
