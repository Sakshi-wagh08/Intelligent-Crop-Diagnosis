import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from backend.app.schemas.soil import (
    SoilTelemetryParameters,
    SoilTelemetryResponse,
    SoilWaterRetention,
    SoilUncertaintyInfo,
)
from backend.app.telemetry.exceptions import InvalidCoordinatesError

logger = logging.getLogger(__name__)

STANDARD_UNITS: Dict[str, str] = {
    "pH": "dimensionless (-)",
    "organic_carbon_g_kg": "g/kg",
    "nitrogen_cg_kg": "cg/kg",
    "nitrogen_g_kg": "g/kg",
    "cation_exchange_capacity_cmol_kg": "cmol(+)/kg",
    "sand_fraction_percent": "%",
    "silt_fraction_percent": "%",
    "clay_fraction_percent": "%",
    "soil_texture_class": "USDA texture class",
    "water_retention_fc_10kpa": "% vol",
    "water_retention_fc_33kpa": "% vol",
    "water_retention_wp_1500kpa": "% vol",
    "available_water_capacity": "% vol",
}

DISCLAIMER_MODELED_ESTIMATE = (
    "Modeled Estimate: Soil parameters are digital soil mapping predictions at 250m gridded resolution "
    "(ISRIC SoilGrids 2.0 / Poggio et al., 2021). They are statistical model outputs, NOT laboratory measurements. "
    "Total nitrogen represents total chemical reserves and does NOT represent immediately plant-available "
    "mineral nitrogen (NO3- / NH4+). Water retention values represent matrix storage capacities, NOT dynamic field moisture."
)


def validate_wgs84_coordinates(latitude: float, longitude: float) -> None:
    """Validates that latitude and longitude fall within legal WGS-84 coordinate bounds."""
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise InvalidCoordinatesError(latitude, longitude, "Coordinates must be numerical values")
    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise InvalidCoordinatesError(latitude, longitude)


def classify_usda_texture(
    sand: Optional[float],
    silt: Optional[float],
    clay: Optional[float],
) -> Optional[str]:
    """Determines the standard USDA soil textural class from sand, silt, and clay percentages.

    Follows the USDA Natural Resources Conservation Service (NRCS) soil texture triangle.
    Sand, silt, and clay percentages must sum to approximately 100%.
    """
    if sand is None or silt is None or clay is None:
        return None

    total = sand + silt + clay
    if total <= 0:
        return None

    # Normalize to exactly 100% to handle floating point discrepancies
    s = (sand / total) * 100.0
    si = (silt / total) * 100.0
    c = (clay / total) * 100.0

    # USDA NRCS classification boundaries
    if c >= 40.0 and s <= 45.0 and si < 40.0:
        return "Clay"
    if c >= 40.0 and si >= 40.0:
        return "Silty Clay"
    if c >= 35.0 and s > 45.0:
        return "Sandy Clay"
    if 27.0 <= c < 40.0 and 20.0 < s <= 45.0:
        return "Clay Loam"
    if 27.0 <= c < 40.0 and s <= 20.0:
        return "Silty Clay Loam"
    if 20.0 <= c < 35.0 and si < 28.0 and s > 45.0:
        return "Sandy Clay Loam"
    if 7.0 <= c < 27.0 and 28.0 <= si < 50.0 and s <= 52.0:
        return "Loam"
    if (si >= 50.0 and 12.0 <= c < 27.0) or (50.0 <= si < 80.0 and c < 12.0):
        return "Silt Loam"
    if si >= 80.0 and c < 12.0:
        return "Silt"
    if s >= 85.0 and (si + 1.5 * c) < 15.0:
        return "Sand"
    if 70.0 <= s <= 90.0 and (si + 1.5 * c) >= 15.0 and (si + 2.0 * c) <= 30.0:
        return "Loamy Sand"
    if (c < 20.0 and s > 52.0 and (si + 2.0 * c) >= 30.0) or (c < 7.0 and si < 50.0 and 43.0 <= s <= 52.0):
        return "Sandy Loam"

    # Default boundary fallback
    if c >= 35.0:
        return "Clay"
    if s >= 50.0:
        return "Sandy Loam"
    return "Loam"


def process_soilgrids_layers(
    raw_data: Dict[str, Any],
    depth_label: str = "0-5cm",
) -> Tuple[Optional[SoilTelemetryParameters], Optional[Dict[str, SoilUncertaintyInfo]]]:
    """Processes raw SoilGrids layers, applying conversion factors (d_factor) and deriving metrics.

    Returns:
        Tuple of (SoilTelemetryParameters, Dict[str, SoilUncertaintyInfo])
        If all essential values are null (e.g., ocean or masked urban surface), returns (None, None).
    """
    layers: List[Dict[str, Any]] = raw_data.get("layers", [])
    if not layers and isinstance(raw_data.get("properties"), dict):
        layers = raw_data["properties"].get("layers", [])
    if not layers:
        return None, None

    extracted_means: Dict[str, Optional[float]] = {}
    uncertainties: Dict[str, SoilUncertaintyInfo] = {}

    for layer in layers:
        prop_name = layer.get("name")
        unit_measure = layer.get("unit_measure", {})
        d_factor = unit_measure.get("d_factor", 1) or 1

        depths = layer.get("depths", [])
        matched_depth = None
        for d in depths:
            if d.get("label") == depth_label:
                matched_depth = d
                break
        if not matched_depth and depths:
            matched_depth = depths[0]

        if not matched_depth:
            continue

        raw_values = matched_depth.get("values", {})
        raw_mean = raw_values.get("mean")
        raw_median = raw_values.get("Q0.5")
        raw_q05 = raw_values.get("Q0.05")
        raw_q95 = raw_values.get("Q0.95")
        raw_unc = raw_values.get("uncertainty")

        # Scale by d_factor if value is non-null
        def scale(val: Optional[float]) -> Optional[float]:
            if val is None:
                return None
            return round(val / float(d_factor), 2)

        scaled_mean = scale(raw_mean)
        extracted_means[prop_name] = scaled_mean

        if any(v is not None for v in (raw_mean, raw_median, raw_q05, raw_q95, raw_unc)):
            uncertainties[prop_name] = SoilUncertaintyInfo(
                mean=scaled_mean,
                median_q50=scale(raw_median),
                q05=scale(raw_q05),
                q95=scale(raw_q95),
                uncertainty=scale(raw_unc) if raw_unc is not None else None,
            )

    # Check if all returned properties are null (masked terrain)
    if all(v is None for v in extracted_means.values()):
        return None, None

    # Soil texture fractions (scaled in %)
    sand = extracted_means.get("sand")
    silt = extracted_means.get("silt")
    clay = extracted_means.get("clay")
    texture_class = classify_usda_texture(sand, silt, clay)

    # Nitrogen conversions:
    # SoilGrids returns nitrogen in cg/kg (d_factor=100 -> g/kg)
    # E.g. raw 147 -> scaled_mean = 1.47 g/kg, cg/kg = 147.0
    nitrogen_g_kg = extracted_means.get("nitrogen")
    nitrogen_cg_kg = round(nitrogen_g_kg * 100.0, 1) if nitrogen_g_kg is not None else None

    # Hydraulic water retention properties (scaled in % vol)
    wv10 = extracted_means.get("wv0010")
    wv33 = extracted_means.get("wv0033")
    wv1500 = extracted_means.get("wv1500")

    awc = None
    if wv33 is not None and wv1500 is not None:
        awc = max(0.0, round(wv33 - wv1500, 2))

    water_retention = None
    if any(v is not None for v in (wv10, wv33, wv1500, awc)):
        water_retention = SoilWaterRetention(
            field_capacity_10kpa_percent=wv10,
            field_capacity_33kpa_percent=wv33,
            wilting_point_1500kpa_percent=wv1500,
            available_water_capacity_percent=awc,
        )

    # Soil moisture estimate capacity fraction (0.0 to 1.0)
    moisture_estimate = None
    if wv33 is not None:
        moisture_estimate = round(wv33 / 100.0, 3)

    params = SoilTelemetryParameters(
        pH=extracted_means.get("phh2o"),
        organic_carbon_g_kg=extracted_means.get("soc"),
        nitrogen_cg_kg=nitrogen_cg_kg,
        nitrogen_g_kg=nitrogen_g_kg,
        cation_exchange_capacity_cmol_kg=extracted_means.get("cec"),
        sand_fraction_percent=sand,
        silt_fraction_percent=silt,
        clay_fraction_percent=clay,
        soil_texture_class=texture_class,
        soil_moisture_estimate=moisture_estimate,
        water_retention=water_retention,
    )

    return params, uncertainties
