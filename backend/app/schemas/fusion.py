from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.vision import DiagnosisResult, SeverityResult


class DosageCalculationBreakdown(BaseModel):
    """Detailed mathematical breakdown of the dosage calculation D = D0 * Fs * Fv."""
    base_dose_D0: float = Field(..., description="Official base dosage recommended for crop stage")
    dose_unit: str = Field(..., description="Physical dosage unit (e.g. kg/acre, L/acre)")
    soil_factor_Fs: float = Field(..., description="Soil correction factor (1.0 if neutral/disabled)")
    soil_factor_status: str = Field(..., description="Status of soil correction (e.g. 'Active', 'Disabled (Foliar application)', 'Disabled (Soil data unavailable)')")
    severity_factor_Fv: float = Field(..., description="Severity correction factor based on foliar lesion area")
    severity_factor_status: str = Field(..., description="Status of severity correction (e.g. 'Active', 'Neutral (Trace infection)', 'Disabled (Unreliable segmentation)')")
    raw_calculated_dose: float = Field(..., description="D_raw = D0 * Fs * Fv prior to label capping")
    max_label_dose_cap: float = Field(..., description="Statutory maximum label dosage D_label_max")
    final_prescribed_dose: float = Field(..., description="Final bounded dosage D = min(D_raw, D_label_max)")
    water_dilution_liters_per_acre: float = Field(..., description="Recommended water dilution spray volume per acre")
    is_capped_by_label_max: bool = Field(..., description="True if D_raw exceeded D_label_max and was truncated")
    formula_expression: str = Field(
        "D = min(D0 * Fs * Fv, D_label_max)",
        description="Standard mathematical formulation"
    )


class TreatmentDetail(BaseModel):
    """Specific agronomic chemical treatment specification."""
    active_ingredient: str
    registered_product_name: Optional[str] = None
    chemical_family: Optional[str] = None
    reference_concentration_Cr: float
    concentration_unit: str
    crop_stage: str
    application_method: str
    phi_days: int
    ppe_requirements: str
    label_restrictions: str
    source_citation: str
    official_document: Optional[str] = None
    official_citation_detail: Optional[str] = None
    statutory_source_url: Optional[str] = None
    verification_status: str  # "VERIFIED" or "DEMONSTRATION_UNVERIFIED"


class SafetyAssessment(BaseModel):
    """Compliance and safety evaluation for chemical treatment."""
    is_safe_to_apply: bool
    safety_status: str  # "APPROVED", "REJECTED_LOW_CONFIDENCE", "REJECTED_PHI_VIOLATION", "REJECTED_INCOMPATIBILITY", "REJECTED_UNVERIFIED", "NO_TREATMENT_NEEDED"
    confidence_check_passed: bool
    phi_check_passed: bool
    compatibility_check_passed: bool
    verification_check_passed: bool
    warnings: List[str] = []
    protective_equipment: List[str] = []
    environmental_precautions: str


class TelemetryFusionSummary(BaseModel):
    """Summary of all multimodal telemetry inputs used in fusion."""
    crop: str
    disease: str
    diagnostic_confidence: float
    is_healthy: bool
    severity_ratio: float
    severity_tier: str
    severity_is_reliable: bool
    soil_data_status: str  # "live", "cached", "fallback", "unavailable"
    soil_source: str
    soil_pH: Optional[float] = None
    soil_texture: Optional[str] = None
    soil_organic_carbon_g_kg: Optional[float] = None


class FusionRecommendationResponse(BaseModel):
    """Comprehensive recommendation output from the multimodal fusion engine."""
    recommendation_available: bool
    status: str
    status_message: str
    telemetry_summary: TelemetryFusionSummary
    safety_assessment: SafetyAssessment
    treatment: Optional[TreatmentDetail] = None
    dosage_breakdown: Optional[DosageCalculationBreakdown] = None
    advisory_notice: str


class FusionDirectRequest(BaseModel):
    """Direct request payload for pre-diagnosed telemetry fusion."""
    crop_name: str
    crop_stage: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    days_to_harvest: Optional[int] = Field(None, ge=0, description="Estimated days until crop harvest")
    tank_mix_partners: List[str] = Field(default_factory=list, description="Intended co-applied chemicals")
    diagnosed_disease: Optional[str] = Field(None, description="Diagnosed disease (if bypassing vision upload)")
    diagnostic_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    lesion_severity_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    severity_tier: Optional[str] = Field("Low", description="Severity tier if known")
