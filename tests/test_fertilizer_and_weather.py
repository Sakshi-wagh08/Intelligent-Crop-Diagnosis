"""Tests for soil-driven fertilizer rules (Fs), weather spray advisory, and farmer summary."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.app.schemas.soil import SoilTelemetryResponse, SoilTelemetryParameters
from backend.app.fusion.knowledge_base import AgronomicKnowledgeBase
from backend.app.fusion.engine import DosageCalculator
from backend.app.fusion.service import FusionService
from backend.app.telemetry.weather import get_spray_weather_advisory


def test_soil_applied_fertilizer_dynamic_fs_low_oc_and_sandy():
    """Verifies soil-applied Urea adjusts Fs based on soil organic carbon and sand leaching guard."""
    plan = AgronomicKnowledgeBase.get_fertilizer_plan("Tomato", "Vegetative")
    assert plan is not None
    assert plan["active_ingredient"] == "Urea"

    soil_low_oc_sandy = SoilTelemetryResponse(
        latitude=12.52,
        longitude=76.90,
        telemetry_source="ISRIC_SoilGrids_2.0",
        data_status="live",
        is_fallback=False,
        retrieval_timestamp="2026-11-28T00:00:00Z",
        parameters=SoilTelemetryParameters(
            pH=6.2,
            organic_carbon_g_kg=3.5,
            sand_fraction_percent=70.0,
        ),
        advisory_notice="Modeled",
    )

    calc = DosageCalculator.compute_dosage(plan, soil_result=soil_low_oc_sandy)
    # 1.0 * 1.15 (low OC) * 0.90 (sandy leaching guard) = 1.035 -> 1.03 (float rounding)
    assert calc.soil_factor_Fs == 1.03
    assert "Active" in calc.soil_factor_status
    assert calc.final_prescribed_dose <= calc.max_label_dose_cap


def test_soil_applied_fertilizer_dynamic_fs_rich_soil():
    """Verifies rich organic carbon soil reduces Urea Fs to prevent excess application."""
    plan = AgronomicKnowledgeBase.get_fertilizer_plan("Rice", "Tillering")
    assert plan is not None

    soil_rich = SoilTelemetryResponse(
        latitude=12.52,
        longitude=76.90,
        telemetry_source="ISRIC_SoilGrids_2.0",
        data_status="live",
        is_fallback=False,
        retrieval_timestamp="2026-11-28T00:00:00Z",
        parameters=SoilTelemetryParameters(
            pH=6.6,
            organic_carbon_g_kg=15.0,
            sand_fraction_percent=30.0,
        ),
        advisory_notice="Modeled",
    )

    calc = DosageCalculator.compute_dosage(plan, soil_result=soil_rich)
    assert calc.soil_factor_Fs == 0.85
    assert calc.final_prescribed_dose == round(plan["base_dose_D0"] * 0.85, 3)


@pytest.mark.anyio
async def test_healthy_crop_includes_fertilizer_and_farmer_summary():
    """Healthy plants suppress pesticides while returning soil-based fertilizer & simple farmer summary."""
    mock_soil = MagicMock()
    mock_soil.get_telemetry = AsyncMock(return_value=SoilTelemetryResponse(
        latitude=12.52,
        longitude=76.90,
        telemetry_source="Regional_Agronomic_Fallback",
        data_status="fallback",
        is_fallback=True,
        retrieval_timestamp="2026-11-28T00:00:00Z",
        parameters=SoilTelemetryParameters(pH=6.2, organic_carbon_g_kg=4.5, sand_fraction_percent=40.0),
        advisory_notice="Fallback",
    ))

    with patch("backend.app.fusion.service.get_spray_weather_advisory", new=AsyncMock(return_value={
        "weather_status": "live",
        "is_good_to_spray": True,
        "advisory": "Good weather to spray now.",
    })):
        svc = FusionService(soil_svc=mock_soil)
        resp = await svc.fuse_and_recommend(
            crop_name="Tomato",
            crop_stage="Vegetative",
            latitude=12.52,
            longitude=76.90,
            diagnosed_disease_override="healthy",
            diagnostic_confidence_override=0.96,
        )

    assert resp.status == "HEALTHY_NO_TREATMENT_NEEDED"
    assert resp.safety_assessment.is_safe_to_apply is False
    assert resp.treatment is None
    assert resp.fertilizer_recommendation is not None
    assert resp.fertilizer_recommendation["active_ingredient"] == "Urea"
    assert resp.fertilizer_recommendation["soil_factor_Fs"] == 1.15
    assert resp.farmer_summary is not None
    assert "healthy" in resp.farmer_summary["headline"].lower()
    assert len(resp.farmer_summary["speech_text"]) > 10


@pytest.mark.anyio
async def test_weather_advisory_graceful_offline_fallback():
    """Weather client degrades cleanly without crashing when network is unreachable."""
    from backend.app.telemetry import weather
    weather._WEATHER_CACHE.clear()
    with patch("backend.app.telemetry.weather.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = RuntimeError("Network offline")
        adv = await get_spray_weather_advisory(55.55, 66.66)

    assert adv["weather_status"] == "unavailable"
    assert adv["is_good_to_spray"] is None
    assert "windy" in adv["advisory"].lower()


def test_fertilizer_api_endpoint(client: TestClient):
    """Verifies GET /api/v1/fusion/fertilizer returns soil-adjusted fertilizer dosage."""
    with patch("backend.app.telemetry.service.soil_telemetry_service.get_telemetry", new=AsyncMock(return_value=SoilTelemetryResponse(
        latitude=12.52,
        longitude=76.90,
        telemetry_source="Regional_Agronomic_Fallback",
        data_status="fallback",
        is_fallback=True,
        retrieval_timestamp="2026-11-28T00:00:00Z",
        parameters=SoilTelemetryParameters(pH=6.2, organic_carbon_g_kg=4.8, sand_fraction_percent=45.0),
        advisory_notice="Fallback",
    ))):
        resp = client.get("/api/v1/fusion/fertilizer?crop_name=Potato&crop_stage=Vegetative&latitude=12.52&longitude=76.90&field_area_acres=2.0")

    assert resp.status_code == 200
    data = resp.json()
    assert data["active_ingredient"] == "Urea"
    assert data["soil_factor_Fs"] == 1.15
    assert data["total_field_quantity"] == round(data["final_prescribed_dose"] * 2.0, 2)
