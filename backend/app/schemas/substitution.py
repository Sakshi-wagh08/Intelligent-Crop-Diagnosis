from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class RankingWeights(BaseModel):
    """Configurable weights for multi-criteria agro-dealer and product ranking."""
    price: float = Field(0.40, ge=0.0, le=1.0, description="Weight for product price / purchase affordability")
    distance: float = Field(0.35, ge=0.0, le=1.0, description="Weight for geographic proximity (distance)")
    stock: float = Field(0.25, ge=0.0, le=1.0, description="Weight for dealer inventory availability")

    @field_validator("stock")
    @classmethod
    def validate_sum_nonzero(cls, v: float, info) -> float:
        price = info.data.get("price", 0.40)
        distance = info.data.get("distance", 0.35)
        if (price + distance + v) <= 0.0:
            raise ValueError("Sum of ranking weights must be strictly greater than 0.0")
        return v


class ScoreBreakdown(BaseModel):
    """Detailed transparency breakdown of the multi-factor normalized ranking score."""
    price_score: float = Field(..., description="Normalized affordability utility [0.0 - 1.0]")
    distance_score: float = Field(..., description="Normalized proximity utility [0.0 - 1.0]")
    stock_score: float = Field(..., description="Normalized inventory fulfillment utility [0.0 - 1.0]")
    weights_applied: Dict[str, float] = Field(..., description="Weights used during ranking computation")


class SubstitutionCalculationRequest(BaseModel):
    """Standalone payload for calculating chemical substitution quantities."""
    reference_dose_Qr: float = Field(..., gt=0.0, description="Reference baseline dose Qr per acre")
    reference_concentration_Cr: float = Field(..., gt=0.0, description="Reference active ingredient concentration Cr (%)")
    substitute_concentration_Cs: float = Field(..., gt=0.0, description="Substitute product concentration Cs (%)")
    reference_dose_unit: str = Field("kg/acre", description="Physical dosage unit (e.g., kg/acre, L/acre)")
    concentration_unit_Cr: str = Field("%", description="Concentration unit of reference formulation")
    concentration_unit_Cs: str = Field("%", description="Concentration unit of substitute formulation")
    field_area_acres: float = Field(1.0, gt=0.0, description="Field area in acres")
    package_size_str: Optional[str] = Field(None, description="Retail package size string, e.g. '1 kg', '500 g', '500 mL'")
    product_price: Optional[float] = Field(None, ge=0.0, description="Unit retail price per package")


class SubstitutionCalculationResponse(BaseModel):
    """Detailed response for chemical substitution calculation Qs = Qr * (Cr / Cs)."""
    reference_dose_Qr: float
    reference_concentration_Cr: float
    substitute_concentration_Cs: float
    concentration_ratio: float
    substitute_dose_Qs: float
    dose_unit: str
    field_area_acres: float
    total_substitute_quantity: float
    package_size_parsed: Optional[str] = None
    packages_needed: Optional[int] = None
    estimated_total_cost: Optional[float] = None
    currency: str = "INR"
    formula_expression: str = "Qs = Qr * (Cr / Cs)"
    explanation: str


class RankedProductOffering(BaseModel):
    """Individual ranked dealer offering with calculated substitute quantity and explainability."""
    rank: int = Field(..., description="Rank position (1 = best recommendation)")
    composite_score: float = Field(..., description="Normalized multi-criteria score [0.0 - 1.0]")
    merchant_id: int
    merchant_name: str
    contact_phone: str
    address: str
    distance_km: float = Field(..., description="Geodesic distance from farmer location in kilometers")
    product_id: int
    brand_name: str
    active_ingredient: str
    concentration_Cs: float
    concentration_unit: str = "%"
    formulation_type: str
    package_size: str
    unit_price: float
    currency: str = "INR"
    stock_quantity: int
    registration_number: str
    is_legally_registered: bool
    substitute_dose_Qs: float = Field(..., description="Equivalent substitute dose per acre")
    dose_unit: str
    packages_needed: int = Field(..., description="Number of retail packages required for specified field area")
    estimated_total_cost: float = Field(..., description="Total cost to purchase required packages")
    score_breakdown: ScoreBreakdown
    ranking_explanation: str
    is_demo: bool = True


class IneligibleProductOffering(BaseModel):
    """Dealer candidate that was excluded due to regulatory, stock, or formulation constraints."""
    merchant_id: Optional[int] = None
    merchant_name: str
    product_id: Optional[int] = None
    brand_name: str
    active_ingredient: str
    distance_km: Optional[float] = None
    ineligibility_reason: str


class SubstituteAndRankRequest(BaseModel):
    """Complete payload for nearby merchant search, product substitution, and multi-criteria ranking."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Farmer field latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Farmer field longitude (-180 to 180)")
    crop_name: str = Field(..., description="Target agricultural crop, e.g. Tomato")
    disease_name: str = Field(..., description="Diagnosed pathology, e.g. Early Blight")
    active_ingredient: str = Field(..., description="Required chemical active ingredient, e.g. Mancozeb")
    reference_dose_Qr: float = Field(..., gt=0.0, description="Reference baseline dose Qr per acre")
    reference_concentration_Cr: float = Field(..., gt=0.0, description="Reference concentration Cr (%)")
    reference_dose_unit: str = Field("kg/acre", description="Reference dosage unit (kg/acre, L/acre)")
    prescribed_application_method: str = Field("Foliar Spray", description="Required application method")
    field_area_acres: float = Field(1.0, gt=0.0, le=10000.0, description="Field area in acres")
    max_distance_km: float = Field(25.0, gt=0.0, le=200.0, description="Search radius in kilometers (d_max)")
    weights: Optional[RankingWeights] = Field(default_factory=RankingWeights)
    allow_demo: bool = Field(True, description="Whether to include demonstration agro-dealers")


class SubstituteAndRankResponse(BaseModel):
    """Comprehensive dealer recommendation response containing ranked and ineligible candidate breakdowns."""
    status: str
    message: str
    farmer_location: Dict[str, float]
    search_radius_km: float
    target_crop: str
    target_disease: str
    reference_active_ingredient: str
    reference_dose_Qr: float
    reference_dose_unit: str
    reference_concentration_Cr: float
    field_area_acres: float
    total_merchants_searched: int
    total_eligible_products: int
    ranked_offerings: List[RankedProductOffering]
    ineligible_candidates: List[IneligibleProductOffering]
    weights_configured: Dict[str, float]
    demonstration_advisory: str
