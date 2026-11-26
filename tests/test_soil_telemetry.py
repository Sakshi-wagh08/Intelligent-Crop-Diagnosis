import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import httpx
from fastapi.testclient import TestClient

from backend.app.telemetry.exceptions import (
    InvalidCoordinatesError,
    SoilGridsAPIError,
    SoilGridsTimeoutError,
)
from backend.app.telemetry.soilgrids import SoilGridsClient
from backend.app.telemetry.processing import (
    validate_wgs84_coordinates,
    classify_usda_texture,
    process_soilgrids_layers,
    STANDARD_UNITS,
)
from backend.app.telemetry.cache import SpatialSoilCache, round_to_grid
from backend.app.telemetry.fallback import RegionalSoilFallback, REGIONAL_BENCHMARKS
from backend.app.telemetry.service import SoilTelemetryService
from backend.app.schemas.soil import SoilTelemetryParameters, SoilWaterRetention

MOCK_SOILGRIDS_FEATURE = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [77.0, 13.0]},
    "properties": {
        "layers": [
            {
                "name": "phh2o",
                "unit_measure": {"d_factor": 10, "mapped_units": "pH*10", "target_units": "-"},
                "depths": [{"label": "0-5cm", "values": {"mean": 65, "Q0.05": 52, "Q0.5": 64, "Q0.95": 82, "uncertainty": 5}}],
            },
            {
                "name": "soc",
                "unit_measure": {"d_factor": 10, "mapped_units": "dg/kg", "target_units": "g/kg"},
                "depths": [{"label": "0-5cm", "values": {"mean": 193, "Q0.05": 29, "Q0.5": 102, "Q0.95": 392, "uncertainty": 36}}],
            },
            {
                "name": "nitrogen",
                "unit_measure": {"d_factor": 100, "mapped_units": "cg/kg", "target_units": "g/kg"},
                "depths": [{"label": "0-5cm", "values": {"mean": 147, "Q0.05": 30, "Q0.5": 80, "Q0.95": 460, "uncertainty": None}}],
            },
            {
                "name": "cec",
                "unit_measure": {"d_factor": 10, "mapped_units": "mmol(c)/kg", "target_units": "cmol(c)/kg"},
                "depths": [{"label": "0-5cm", "values": {"mean": 164, "Q0.05": 29, "Q0.5": 84, "Q0.95": 545, "uncertainty": 61}}],
            },
            {
                "name": "sand",
                "unit_measure": {"d_factor": 10, "mapped_units": "g/kg", "target_units": "%"},
                "depths": [{"label": "0-5cm", "values": {"mean": 494, "Q0.05": 112, "Q0.5": 563, "Q0.95": 785, "uncertainty": 12}}],
            },
            {
                "name": "silt",
                "unit_measure": {"d_factor": 10, "mapped_units": "g/kg", "target_units": "%"},
                "depths": [{"label": "0-5cm", "values": {"mean": 220, "Q0.05": 27, "Q0.5": 132, "Q0.95": 689, "uncertainty": 50}}],
            },
            {
                "name": "clay",
                "unit_measure": {"d_factor": 10, "mapped_units": "g/kg", "target_units": "%"},
                "depths": [{"label": "0-5cm", "values": {"mean": 286, "Q0.05": 50, "Q0.5": 176, "Q0.95": 825, "uncertainty": 44}}],
            },
            {
                "name": "wv0010",
                "unit_measure": {"d_factor": 10, "mapped_units": "(10-2 cm3/cm3)*10", "target_units": "10-2 cm3/cm3"},
                "depths": [{"label": "0-5cm", "values": {"mean": 387, "Q0.05": 215, "Q0.5": 392, "Q0.95": 502, "uncertainty": 7}}],
            },
            {
                "name": "wv0033",
                "unit_measure": {"d_factor": 10, "mapped_units": "(10-2 cm3/cm3)*10", "target_units": "10-2 cm3/cm3"},
                "depths": [{"label": "0-5cm", "values": {"mean": 302, "Q0.05": 112, "Q0.5": 309, "Q0.95": 507, "uncertainty": 13}}],
            },
            {
                "name": "wv1500",
                "unit_measure": {"d_factor": 10, "mapped_units": "(10-2 cm3/cm3)*10", "target_units": "10-2 cm3/cm3"},
                "depths": [{"label": "0-5cm", "values": {"mean": 121, "Q0.05": 40, "Q0.5": 86, "Q0.95": 295, "uncertainty": 30}}],
            },
        ]
    },
    "query_time_s": 0.35,
}


# ==============================================================================
# 1. Coordinate Validation Tests
# ==============================================================================

def test_coordinate_validation_valid_ranges():
    """Confirms valid WGS-84 coordinates pass without exception."""
    validate_wgs84_coordinates(0.0, 0.0)
    validate_wgs84_coordinates(90.0, 180.0)
    validate_wgs84_coordinates(-90.0, -180.0)
    validate_wgs84_coordinates(12.9716, 77.5946)


def test_coordinate_validation_invalid_bounds():
    """Confirms out-of-range coordinates raise InvalidCoordinatesError."""
    with pytest.raises(InvalidCoordinatesError):
        validate_wgs84_coordinates(90.1, 77.0)

    with pytest.raises(InvalidCoordinatesError):
        validate_wgs84_coordinates(-90.1, 77.0)

    with pytest.raises(InvalidCoordinatesError):
        validate_wgs84_coordinates(12.0, 180.1)

    with pytest.raises(InvalidCoordinatesError):
        validate_wgs84_coordinates(12.0, -180.1)


# ==============================================================================
# 2. USDA Soil Textural Classification Tests
# ==============================================================================

def test_usda_texture_classification():
    """Validates USDA soil texture classification triangle logic."""
    assert classify_usda_texture(sand=90.0, silt=5.0, clay=5.0) == "Sand"
    assert classify_usda_texture(sand=80.0, silt=10.0, clay=10.0) == "Loamy Sand"
    assert classify_usda_texture(sand=60.0, silt=25.0, clay=15.0) == "Sandy Loam"
    assert classify_usda_texture(sand=40.0, silt=40.0, clay=20.0) == "Loam"
    assert classify_usda_texture(sand=20.0, silt=65.0, clay=15.0) == "Silt Loam"
    assert classify_usda_texture(sand=5.0, silt=85.0, clay=10.0) == "Silt"
    assert classify_usda_texture(sand=60.0, silt=15.0, clay=25.0) == "Sandy Clay Loam"
    assert classify_usda_texture(sand=30.0, silt=35.0, clay=35.0) == "Clay Loam"
    assert classify_usda_texture(sand=10.0, silt=55.0, clay=35.0) == "Silty Clay Loam"
    assert classify_usda_texture(sand=50.0, silt=10.0, clay=40.0) == "Sandy Clay"
    assert classify_usda_texture(sand=10.0, silt=45.0, clay=45.0) == "Silty Clay"
    assert classify_usda_texture(sand=20.0, silt=20.0, clay=60.0) == "Clay"


def test_usda_texture_missing_or_invalid():
    """Validates texture classifier handles None or zero values gracefully."""
    assert classify_usda_texture(None, 40.0, 20.0) is None
    assert classify_usda_texture(0.0, 0.0, 0.0) is None


# ==============================================================================
# 3. Processing and Unit Conversion Tests
# ==============================================================================

def test_process_soilgrids_layers_unit_conversion():
    """Validates d_factor scaling, quantiles, and derived water retention metrics."""
    params, uncertainties = process_soilgrids_layers(MOCK_SOILGRIDS_FEATURE, depth_label="0-5cm")

    assert params is not None
    assert uncertainties is not None

    # pH scaled by d_factor 10: 65 / 10 = 6.5
    assert params.pH == 6.5

    # SOC scaled by d_factor 10: 193 / 10 = 19.3 g/kg
    assert params.organic_carbon_g_kg == 19.3

    # Nitrogen: raw mean 147 -> d_factor 100 -> 1.47 g/kg; cg/kg = 147.0
    assert params.nitrogen_g_kg == 1.47
    assert params.nitrogen_cg_kg == 147.0

    # CEC scaled by 10: 164 / 10 = 16.4 cmol(+)/kg
    assert params.cation_exchange_capacity_cmol_kg == 16.4

    # Sand 49.4%, Silt 22.0%, Clay 28.6%
    assert params.sand_fraction_percent == 49.4
    assert params.silt_fraction_percent == 22.0
    assert params.clay_fraction_percent == 28.6
    assert params.soil_texture_class == "Sandy Clay Loam"

    # Hydraulic water retention
    assert params.water_retention is not None
    assert params.water_retention.field_capacity_10kpa_percent == 38.7
    assert params.water_retention.field_capacity_33kpa_percent == 30.2
    assert params.water_retention.wilting_point_1500kpa_percent == 12.1
    # AWC = 30.2 - 12.1 = 18.1
    assert params.water_retention.available_water_capacity_percent == 18.1
    assert params.soil_moisture_estimate == 0.302

    # Uncertainty quantiles preserved
    assert "phh2o" in uncertainties
    assert uncertainties["phh2o"].mean == 6.5
    assert uncertainties["phh2o"].q05 == 5.2
    assert uncertainties["phh2o"].median_q50 == 6.4
    assert uncertainties["phh2o"].q95 == 8.2
    assert uncertainties["phh2o"].uncertainty == 0.5


def test_process_soilgrids_masked_all_nulls():
    """Validates that terrain with null values (ocean / masked urban) returns (None, None)."""
    masked_data = {
        "layers": [
            {
                "name": "phh2o",
                "unit_measure": {"d_factor": 10},
                "depths": [{"label": "0-5cm", "values": {"mean": None, "Q0.5": None}}],
            },
            {
                "name": "soc",
                "unit_measure": {"d_factor": 10},
                "depths": [{"label": "0-5cm", "values": {"mean": None, "Q0.5": None}}],
            },
        ]
    }
    params, uncs = process_soilgrids_layers(masked_data, "0-5cm")
    assert params is None
    assert uncs is None


# ==============================================================================
# 4. Spatial Caching Tests
# ==============================================================================

def test_spatial_grid_rounding():
    """Confirms ~500m coordinate rounding maps nearby coordinates to identical grid cell."""
    # 0.005 deg rounding
    r_lat1 = round_to_grid(12.9716, 0.005)
    r_lat2 = round_to_grid(12.9720, 0.005)
    assert r_lat1 == r_lat2 == 12.97

    r_lon1 = round_to_grid(77.5946, 0.005)
    r_lon2 = round_to_grid(77.5950, 0.005)
    assert r_lon1 == r_lon2 == 77.595


def test_spatial_cache_set_get_and_expiration():
    """Validates cache storage, retrieval, TTL expiration, and purging."""
    cache = SpatialSoilCache(grid_deg=0.005, default_ttl_seconds=2)
    demo_params = SoilTelemetryParameters(pH=6.5, organic_carbon_g_kg=12.0)

    # Set cache
    cache.set(12.9716, 77.5946, "0-5cm", demo_params, source="Test_Source", ttl_seconds=1)
    assert cache.size() == 1

    # Immediate retrieval -> hit
    entry = cache.get(12.9718, 77.5948, "0-5cm")  # Nearby coordinates round to same cell
    assert entry is not None
    assert entry.parameters.pH == 6.5
    assert entry.source == "Test_Source"

    # Simulate expiration by evaluating with future timestamp
    future_time = datetime.now(timezone.utc) + timedelta(seconds=10)
    assert entry.is_expired(future_time) is True

    # Get with expired entry removes it
    with patch("backend.app.telemetry.cache.datetime") as mock_dt:
        mock_dt.now.return_value = future_time
        assert cache.get(12.9716, 77.5946, "0-5cm") is None


# ==============================================================================
# 5. Regional Agronomic Fallback Tests
# ==============================================================================

def test_regional_fallback_identification():
    """Validates Karnataka agro-climatic zone benchmark matching."""
    # Bangalore (Eastern Dry Zone)
    bengaluru_match = RegionalSoilFallback.find_regional_benchmark(12.97, 77.59)
    assert bengaluru_match is not None
    assert "Eastern Dry Zone" in bengaluru_match["zone_name"]

    # Mandya (Southern Dry Zone)
    mandya_match = RegionalSoilFallback.find_regional_benchmark(12.52, 76.89)
    assert mandya_match is not None
    assert "Southern Dry Zone" in mandya_match["zone_name"]

    # Dharwad (Northern Transition Zone)
    dharwad_match = RegionalSoilFallback.find_regional_benchmark(15.45, 75.01)
    assert dharwad_match is not None
    assert "Northern Transition Zone" in dharwad_match["zone_name"]


def test_prevention_of_fabricated_soil_values():
    """Confirms that coordinates outside verified benchmark zones return None (no fake data)."""
    # Atlantic Ocean (0.0, 0.0)
    ocean_match = RegionalSoilFallback.find_regional_benchmark(0.0, 0.0)
    assert ocean_match is None

    # European coordinates (51.5, 0.1)
    europe_match = RegionalSoilFallback.find_regional_benchmark(51.5, 0.1)
    assert europe_match is None

    params, source, advisory = RegionalSoilFallback.get_fallback_telemetry(0.0, 0.0)
    assert params is None
    assert source is None
    assert advisory is None


# ==============================================================================
# 6. Service Integration & Fallback Activation Tests
# ==============================================================================

@pytest.mark.anyio
async def test_soil_service_live_fetch_success():
    """Tests full service flow when live SoilGrids API query succeeds."""
    mock_client = MagicMock(spec=SoilGridsClient)
    mock_client.query_properties = AsyncMock(return_value=MOCK_SOILGRIDS_FEATURE)
    isolated_cache = SpatialSoilCache()

    service = SoilTelemetryService(soilgrids_client=mock_client, cache=isolated_cache)
    response = await service.get_telemetry(latitude=13.0, longitude=77.0, depth="0-5cm")

    assert response.data_status == "live"
    assert response.telemetry_source == "ISRIC_SoilGrids_2.0"
    assert response.is_fallback is False
    assert response.parameters is not None
    assert response.parameters.pH == 6.5
    assert response.parameters.nitrogen_g_kg == 1.47
    assert response.parameters.soil_texture_class == "Sandy Clay Loam"

    # Verify cached
    assert isolated_cache.size() == 1


@pytest.mark.anyio
async def test_soil_service_cache_hit():
    """Tests service serves cached telemetry without hitting client."""
    mock_client = MagicMock(spec=SoilGridsClient)
    mock_client.query_properties = AsyncMock()
    isolated_cache = SpatialSoilCache()

    demo_params = SoilTelemetryParameters(pH=7.0, organic_carbon_g_kg=10.0)
    isolated_cache.set(13.0, 77.0, "0-5cm", demo_params, source="ISRIC_SoilGrids_2.0")

    service = SoilTelemetryService(soilgrids_client=mock_client, cache=isolated_cache)
    response = await service.get_telemetry(latitude=13.001, longitude=77.001, depth="0-5cm")

    assert response.data_status == "cached"
    assert "Spatial_Cache" in response.telemetry_source
    assert response.parameters.pH == 7.0
    # Client should NOT have been called
    mock_client.query_properties.assert_not_called()


@pytest.mark.anyio
async def test_soil_service_timeout_triggers_regional_fallback():
    """Confirms SoilGrids timeout automatically activates regional agronomic fallback."""
    mock_client = MagicMock(spec=SoilGridsClient)
    mock_client.query_properties = AsyncMock(side_effect=SoilGridsTimeoutError(2.0))
    isolated_cache = SpatialSoilCache()

    service = SoilTelemetryService(soilgrids_client=mock_client, cache=isolated_cache)
    # Mandya coordinates (in Southern Dry Zone)
    response = await service.get_telemetry(latitude=12.52, longitude=76.89, depth="0-5cm")

    assert response.data_status == "fallback"
    assert response.is_fallback is True
    assert "Regional_Agronomic_Fallback" in response.telemetry_source
    assert "Southern Dry Zone" in response.telemetry_source
    assert response.parameters is not None
    assert response.parameters.pH == 6.5
    assert "REGIONAL AGRONOMIC FALLBACK" in response.advisory_notice


@pytest.mark.anyio
async def test_soil_service_503_triggers_unavailable_outside_fallback():
    """Confirms external error outside fallback zones returns explicit 'unavailable' status."""
    mock_client = MagicMock(spec=SoilGridsClient)
    mock_client.query_properties = AsyncMock(side_effect=SoilGridsAPIError(status_code=503, details="Service Unavailable"))
    isolated_cache = SpatialSoilCache()

    service = SoilTelemetryService(soilgrids_client=mock_client, cache=isolated_cache)
    # Outside any regional benchmark (Atlantic ocean)
    response = await service.get_telemetry(latitude=0.0, longitude=0.0, depth="0-5cm")

    assert response.data_status == "unavailable"
    assert response.telemetry_source == "Unavailable"
    assert response.parameters is None
    assert "SOIL TELEMETRY UNAVAILABLE" in response.advisory_notice


# ==============================================================================
# 7. End-to-End FastAPI Endpoint Tests
# ==============================================================================

def test_api_soil_telemetry_live_endpoint(client: TestClient):
    """Tests GET /api/v1/soil/telemetry with mocked successful live response."""
    with patch(
        "backend.app.telemetry.service.soil_telemetry_service.client.query_properties",
        new_callable=AsyncMock,
        return_value=MOCK_SOILGRIDS_FEATURE,
    ):
        # Clear cache to guarantee fresh query
        from backend.app.telemetry.service import soil_telemetry_service
        soil_telemetry_service.cache.clear()

        response = client.get("/api/v1/soil/telemetry?latitude=13.0&longitude=77.0&depth=0-5cm")
        assert response.status_code == 200
        data = response.json()

        assert data["latitude"] == 13.0
        assert data["longitude"] == 77.0
        assert data["depth"] == "0-5cm"
        assert data["data_status"] == "live"
        assert data["parameters"]["pH"] == 6.5
        assert data["parameters"]["soil_texture_class"] == "Sandy Clay Loam"
        assert "units" in data
        assert "uncertainty_quantiles" in data
        assert "water_retention" in data["parameters"]


def test_api_soil_telemetry_invalid_coordinates_http_422(client: TestClient):
    """Tests GET /api/v1/soil/telemetry rejects invalid coordinates with HTTP 422."""
    response = client.get("/api/v1/soil/telemetry?latitude=999.0&longitude=77.0")
    assert response.status_code == 422
