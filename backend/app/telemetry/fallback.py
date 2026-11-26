import logging
from typing import Optional, Dict, Any, Tuple
from backend.app.schemas.soil import (
    SoilTelemetryParameters,
    SoilWaterRetention,
    SoilUncertaintyInfo,
)

logger = logging.getLogger(__name__)

# Documented Official Regional Agronomic Benchmarks (ICAR-NBSS&LUP Karnataka Agro-Climatic Zones)
# Reference: National Bureau of Soil Survey and Land Use Planning (ICAR-NBSS&LUP Publ. 47:
# "Soils of Karnataka for Optimising Land Use", Agricultural Research Institute, Bangalore).
REGIONAL_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "karnataka_eastern_dry_zone": {
        "zone_name": "Karnataka Eastern Dry Zone (Zone 5 - Bangalore/Kolar/Chikkaballapura)",
        "citation": "ICAR-NBSS&LUP Publ. 47 (Typic Rhodustalfs Benchmark Profiles)",
        "bounds": {"min_lat": 12.5, "max_lat": 13.8, "min_lon": 77.0, "max_lon": 78.6},
        "parameters": {
            "pH": 6.2,
            "organic_carbon_g_kg": 4.8,
            "nitrogen_cg_kg": 80.0,
            "nitrogen_g_kg": 0.8,
            "cation_exchange_capacity_cmol_kg": 14.2,
            "sand_fraction_percent": 58.0,
            "silt_fraction_percent": 18.0,
            "clay_fraction_percent": 24.0,
            "soil_texture_class": "Sandy Clay Loam",
            "soil_moisture_estimate": 0.21,
            "water_retention": {
                "field_capacity_10kpa_percent": 24.5,
                "field_capacity_33kpa_percent": 21.0,
                "wilting_point_1500kpa_percent": 9.5,
                "available_water_capacity_percent": 11.5,
            },
        },
    },
    "karnataka_southern_dry_zone": {
        "zone_name": "Karnataka Southern Dry Zone (Zone 6 - Mandya/Mysore/Chamarajanagar)",
        "citation": "ICAR-NBSS&LUP Publ. 47 (Kandic Paleustalfs Benchmark Profiles)",
        "bounds": {"min_lat": 11.6, "max_lat": 12.8, "min_lon": 76.0, "max_lon": 77.4},
        "parameters": {
            "pH": 6.5,
            "organic_carbon_g_kg": 5.6,
            "nitrogen_cg_kg": 95.0,
            "nitrogen_g_kg": 0.95,
            "cation_exchange_capacity_cmol_kg": 16.5,
            "sand_fraction_percent": 62.0,
            "silt_fraction_percent": 16.0,
            "clay_fraction_percent": 22.0,
            "soil_texture_class": "Sandy Clay Loam",
            "soil_moisture_estimate": 0.225,
            "water_retention": {
                "field_capacity_10kpa_percent": 25.5,
                "field_capacity_33kpa_percent": 22.5,
                "wilting_point_1500kpa_percent": 10.0,
                "available_water_capacity_percent": 12.5,
            },
        },
    },
    "karnataka_central_dry_zone": {
        "zone_name": "Karnataka Central Dry Zone (Zone 4 - Chitradurga/Davanagere)",
        "citation": "ICAR-NBSS&LUP Publ. 47 (Vertic Ustochrepts Benchmark Profiles)",
        "bounds": {"min_lat": 13.5, "max_lat": 14.8, "min_lon": 75.5, "max_lon": 77.2},
        "parameters": {
            "pH": 7.4,
            "organic_carbon_g_kg": 4.2,
            "nitrogen_cg_kg": 75.0,
            "nitrogen_g_kg": 0.75,
            "cation_exchange_capacity_cmol_kg": 22.0,
            "sand_fraction_percent": 45.0,
            "silt_fraction_percent": 25.0,
            "clay_fraction_percent": 30.0,
            "soil_texture_class": "Clay Loam",
            "soil_moisture_estimate": 0.26,
            "water_retention": {
                "field_capacity_10kpa_percent": 30.0,
                "field_capacity_33kpa_percent": 26.0,
                "wilting_point_1500kpa_percent": 13.0,
                "available_water_capacity_percent": 13.0,
            },
        },
    },
    "karnataka_northern_transition_zone": {
        "zone_name": "Karnataka Northern Transition Zone (Zone 8 - Dharwad/Belagavi/Haveri)",
        "citation": "ICAR-NBSS&LUP Publ. 47 (Typic Chromusterts Deep Black Soil Profiles)",
        "bounds": {"min_lat": 14.5, "max_lat": 16.5, "min_lon": 74.5, "max_lon": 76.2},
        "parameters": {
            "pH": 8.1,
            "organic_carbon_g_kg": 6.2,
            "nitrogen_cg_kg": 110.0,
            "nitrogen_g_kg": 1.1,
            "cation_exchange_capacity_cmol_kg": 42.0,
            "sand_fraction_percent": 22.0,
            "silt_fraction_percent": 32.0,
            "clay_fraction_percent": 46.0,
            "soil_texture_class": "Clay",
            "soil_moisture_estimate": 0.36,
            "water_retention": {
                "field_capacity_10kpa_percent": 41.0,
                "field_capacity_33kpa_percent": 36.0,
                "wilting_point_1500kpa_percent": 21.0,
                "available_water_capacity_percent": 15.0,
            },
        },
    },
    "karnataka_coastal_hilly_zone": {
        "zone_name": "Karnataka Coastal and Hilly Zone (Zones 9 & 10 - Malnad & Coastal Laterites)",
        "citation": "ICAR-NBSS&LUP Publ. 47 (Oxisols / Typic Kandiustults Profiles)",
        "bounds": {"min_lat": 11.9, "max_lat": 15.2, "min_lon": 74.0, "max_lon": 75.8},
        "parameters": {
            "pH": 5.2,
            "organic_carbon_g_kg": 12.5,
            "nitrogen_cg_kg": 150.0,
            "nitrogen_g_kg": 1.5,
            "cation_exchange_capacity_cmol_kg": 11.5,
            "sand_fraction_percent": 50.0,
            "silt_fraction_percent": 24.0,
            "clay_fraction_percent": 26.0,
            "soil_texture_class": "Sandy Clay Loam",
            "soil_moisture_estimate": 0.24,
            "water_retention": {
                "field_capacity_10kpa_percent": 28.0,
                "field_capacity_33kpa_percent": 24.0,
                "wilting_point_1500kpa_percent": 12.0,
                "available_water_capacity_percent": 12.0,
            },
        },
    },
}


class RegionalSoilFallback:
    """Provides documented agronomic benchmark baselines when external services are unavailable."""

    @staticmethod
    def find_regional_benchmark(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Identifies if coordinates fall within a verified regional benchmark zone.

        Strict compliance: Never invents fake regional values. If coordinates fall outside
        any verified regional benchmark zone, returns None.
        """
        for zone_id, data in REGIONAL_BENCHMARKS.items():
            bounds = data["bounds"]
            if (
                bounds["min_lat"] <= latitude <= bounds["max_lat"]
                and bounds["min_lon"] <= longitude <= bounds["max_lon"]
            ):
                return data
        return None

    @classmethod
    def get_fallback_telemetry(
        cls,
        latitude: float,
        longitude: float,
    ) -> Tuple[Optional[SoilTelemetryParameters], Optional[str], Optional[str]]:
        """Retrieves verified fallback parameters for given coordinates.

        Returns:
            Tuple of (SoilTelemetryParameters, source_description, advisory_notice)
            If coordinates are outside verified benchmark areas, returns (None, None, None).
        """
        match = cls.find_regional_benchmark(latitude, longitude)
        if not match:
            logger.info("Coordinates (%s, %s) fall outside documented regional benchmark zones", latitude, longitude)
            return None, None, None

        params_dict = match["parameters"]
        wr_dict = params_dict.get("water_retention", {})
        water_retention = SoilWaterRetention(
            field_capacity_10kpa_percent=wr_dict.get("field_capacity_10kpa_percent"),
            field_capacity_33kpa_percent=wr_dict.get("field_capacity_33kpa_percent"),
            wilting_point_1500kpa_percent=wr_dict.get("wilting_point_1500kpa_percent"),
            available_water_capacity_percent=wr_dict.get("available_water_capacity_percent"),
        )

        parameters = SoilTelemetryParameters(
            pH=params_dict.get("pH"),
            organic_carbon_g_kg=params_dict.get("organic_carbon_g_kg"),
            nitrogen_cg_kg=params_dict.get("nitrogen_cg_kg"),
            nitrogen_g_kg=params_dict.get("nitrogen_g_kg"),
            cation_exchange_capacity_cmol_kg=params_dict.get("cation_exchange_capacity_cmol_kg"),
            sand_fraction_percent=params_dict.get("sand_fraction_percent"),
            silt_fraction_percent=params_dict.get("silt_fraction_percent"),
            clay_fraction_percent=params_dict.get("clay_fraction_percent"),
            soil_texture_class=params_dict.get("soil_texture_class"),
            soil_moisture_estimate=params_dict.get("soil_moisture_estimate"),
            water_retention=water_retention,
        )

        source_desc = f"Regional_Agronomic_Fallback ({match['zone_name']})"
        advisory = (
            f"REGIONAL AGRONOMIC FALLBACK: Live SoilGrids telemetry was unavailable. "
            f"Values are published regional benchmarks from {match['citation']}. "
            "These are macro-regional baseline estimates and MUST NOT be treated as field-specific "
            "laboratory soil test measurements."
        )

        return parameters, source_desc, advisory
