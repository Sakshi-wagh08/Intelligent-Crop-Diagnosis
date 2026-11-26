from typing import Optional, Dict
from pydantic import BaseModel, Field


class SoilUncertaintyInfo(BaseModel):
    """Prediction quantiles and uncertainty metrics for a single soil property."""
    mean: Optional[float] = None
    median_q50: Optional[float] = None
    q05: Optional[float] = None
    q95: Optional[float] = None
    uncertainty: Optional[float] = None


class SoilWaterRetention(BaseModel):
    """Modeled soil water retention characteristics at standard matrix potentials.

    CRITICAL AGRONOMIC NOTICE:
    These values represent physical hydraulic retention capacities (pF curves) of the
    soil matrix. They do NOT represent dynamic real-time field moisture, which requires
    in-situ capacitance/TDR sensors or real-time precipitation-evapotranspiration balances.
    """
    field_capacity_10kpa_percent: Optional[float] = Field(
        None, description="Volumetric water content at 10 kPa matrix potential (coarse drainage limit) in % vol"
    )
    field_capacity_33kpa_percent: Optional[float] = Field(
        None, description="Volumetric water content at 33 kPa matrix potential (standard field capacity) in % vol"
    )
    wilting_point_1500kpa_percent: Optional[float] = Field(
        None, description="Volumetric water content at 1500 kPa matrix potential (permanent wilting point) in % vol"
    )
    available_water_capacity_percent: Optional[float] = Field(
        None, description="Available Water Capacity (AWC = FC_33 - WP_1500) in % vol"
    )


class SoilTelemetryParameters(BaseModel):
    """Soil physical and chemical properties extracted from SoilGrids 2.0 or verified fallback.

    CRITICAL AGRONOMIC NOTICE:
    Total nitrogen represents total chemical nitrogen in organic and inorganic soil reserves.
    It does NOT equate to immediately plant-available mineral nitrogen (NO3- / NH4+).
    """
    pH: Optional[float] = Field(None, description="Soil pH measured in H2O")
    organic_carbon_g_kg: Optional[float] = Field(None, description="Soil organic carbon (soc) in g/kg (permille)")
    nitrogen_cg_kg: Optional[float] = Field(None, description="Total nitrogen in cg/kg")
    nitrogen_g_kg: Optional[float] = Field(None, description="Total nitrogen in g/kg")
    cation_exchange_capacity_cmol_kg: Optional[float] = Field(None, description="Cation exchange capacity at pH 7 (cec) in cmol(+)/kg")
    sand_fraction_percent: Optional[float] = Field(None, description="Sand content (0.05-2mm) in %")
    silt_fraction_percent: Optional[float] = Field(None, description="Silt content (0.002-0.05mm) in %")
    clay_fraction_percent: Optional[float] = Field(None, description="Clay content (<0.002mm) in %")
    soil_texture_class: Optional[str] = Field(None, description="USDA soil texture classification")
    soil_moisture_estimate: Optional[float] = Field(None, description="Estimated soil volumetric moisture content capacity fraction (0.0 - 1.0)")
    water_retention: Optional[SoilWaterRetention] = Field(None, description="Modeled hydraulic matrix retention properties")


class SoilTelemetryResponse(BaseModel):
    """Standardized response schema for remote soil telemetry queries."""
    latitude: float
    longitude: float
    depth: str = Field("0-5cm", description="Target soil depth horizon (e.g. 0-5cm, 5-15cm)")
    telemetry_source: str = Field(..., description="ISRIC_SoilGrids_2.0, Regional_Agronomic_Fallback, or Spatial_Cache")
    data_status: str = Field("live", description="Status indicator: 'live', 'cached', 'fallback', or 'unavailable'")
    is_fallback: bool = Field(False, description="True if regional baseline defaults were applied due to API timeout or missing data")
    retrieval_timestamp: str = Field(..., description="ISO 8601 UTC timestamp of data acquisition")
    parameters: Optional[SoilTelemetryParameters] = Field(None, description="Extracted soil chemical, physical, and hydraulic attributes")
    units: Dict[str, str] = Field(default_factory=dict, description="Standard physical measurement units for parameters")
    uncertainty_level: str = Field("Modeled Estimate (250m gridded resolution)", description="Telemetry uncertainty qualification")
    uncertainty_quantiles: Optional[Dict[str, SoilUncertaintyInfo]] = Field(None, description="Quantiles (Q0.05, Q0.5, Q0.95) and uncertainty when available")
    advisory_notice: str = Field(
        ...,
        description="Agronomic advisory disclaimer regarding modeled estimates vs laboratory testing"
    )
