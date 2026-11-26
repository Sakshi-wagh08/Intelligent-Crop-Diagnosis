from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DiseaseBase(BaseModel):
    """Disease summary schema."""
    id: int
    disease_name: str
    scientific_name: Optional[str] = None
    pathogen_type: str
    symptoms: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CropResponse(BaseModel):
    """Crop details with associated diseases schema."""
    id: int
    name: str
    scientific_name: Optional[str] = None
    description: Optional[str] = None
    diseases: List[DiseaseBase] = []

    model_config = ConfigDict(from_attributes=True)


class ActiveIngredientResponse(BaseModel):
    """Active chemical ingredient schema."""
    id: int
    common_name: str
    chemical_family: Optional[str] = None
    standard_concentration_Cr: float
    concentration_unit: str
    max_legal_dose_cap: float
    phi_days: int
    ppe_requirements: Optional[str] = None
    is_demo: bool

    model_config = ConfigDict(from_attributes=True)


class BaseTreatmentResponse(BaseModel):
    """Agronomic package-of-practices guideline schema."""
    id: int
    crop_stage: str
    base_dose_D0: float
    dose_unit: str
    water_dilution_liters_per_acre: float
    application_method: str
    application_timing: Optional[str] = None
    active_ingredient: ActiveIngredientResponse
    is_demo: bool

    model_config = ConfigDict(from_attributes=True)
