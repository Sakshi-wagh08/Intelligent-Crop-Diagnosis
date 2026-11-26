import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.schemas.vision import DiagnosisResult, SeverityResult
from backend.app.schemas.soil import SoilTelemetryResponse, SoilTelemetryParameters
from backend.app.fusion.knowledge_base import AgronomicKnowledgeBase, VERIFIED_TREATMENTS
from backend.app.fusion.safety import SafetyComplianceEngine
from backend.app.fusion.engine import DosageCalculator
from backend.app.fusion.service import FusionService


# ==============================================================================
# 1. Agronomic Knowledge Base Tests
# ==============================================================================

def test_knowledge_base_verified_treatment_lookup():
    """Validates that verified treatments are properly retrieved with traceable citations."""
    treatment = AgronomicKnowledgeBase.get_treatment(
        crop="Tomato",
        disease="Early Blight",
        stage="Vegetative",
        allow_demo=False,
    )
    assert treatment is not None
    assert treatment["active_ingredient"] == "Mancozeb"
    assert treatment["base_dose_D0"] == 0.80
    assert treatment["max_legal_dose_cap"] == 1.00
    assert treatment["phi_days"] == 14
    assert treatment["verification_status"] == "VERIFIED"
    assert "ICAR-IIHR" in treatment["source_citation"]


def test_knowledge_base_stage_specific_treatment():
    """Validates stage-specific treatment routing (e.g., Azoxystrobin for Flowering Tomato)."""
    treatment = AgronomicKnowledgeBase.get_treatment(
        crop="Tomato",
        disease="Early Blight",
        stage="Flowering",
        allow_demo=False,
    )
    assert treatment is not None
    # For flowering, Azoxystrobin is preferred in knowledge base
    assert treatment["active_ingredient"] == "Azoxystrobin"
    assert treatment["base_dose_D0"] == 0.20
    assert treatment["max_legal_dose_cap"] == 0.25
    assert treatment["phi_days"] == 3


def test_knowledge_base_segregation_of_demonstration_records():
    """Confirms unverified demo records are excluded unless explicitly permitted."""
    # When allow_demo=False, only VERIFIED records are accessible
    treatment = AgronomicKnowledgeBase.get_treatment(
        crop="Tomato",
        disease="Early Blight",
        allow_demo=False,
    )
    assert treatment["verification_status"] == "VERIFIED"


def test_knowledge_base_tank_mix_incompatibility():
    """Validates identification of known chemical incompatibilities."""
    # Mancozeb + Azoxystrobin conflict
    warnings = AgronomicKnowledgeBase.check_incompatibility("Mancozeb", ["Azoxystrobin"])
    assert len(warnings) == 1
    assert "INCOMPATIBILITY DETECTED" in warnings[0]

    # Compatible chemical
    clean_warnings = AgronomicKnowledgeBase.check_incompatibility("Mancozeb", ["Copper Oxychloride"])
    assert len(clean_warnings) == 0


# ==============================================================================
# 2. Dosage Calculation & Bounded Enforcement Tests
# ==============================================================================

def test_dosage_calculation_neutral_baseline():
    """Confirms D = D0 * 1.0 * 1.0 = D0 when severity is low/trace and foliar spray."""
    treatment = {
        "base_dose_D0": 0.80,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 1.00,
        "water_dilution_liters_per_acre": 350.0,
        "application_method": "Foliar Spray",
    }
    severity = SeverityResult(
        lesion_to_leaf_ratio=0.005,
        severity_tier="None / Trace",
        severity_factor_Fv=1.00,
        leaf_pixels=50000,
        lesion_pixels=250,
        leaf_detected=True,
        is_reliable=True,
        status_message="Healthy canopy",
        estimation_disclaimer="Estimated",
    )

    calc = DosageCalculator.compute_dosage(treatment, severity_result=severity)
    assert calc.base_dose_D0 == 0.80
    assert calc.severity_factor_Fv == 1.00
    assert calc.soil_factor_Fs == 1.00
    assert calc.raw_calculated_dose == 0.80
    assert calc.final_prescribed_dose == 0.80
    assert calc.is_capped_by_label_max is False


def test_dosage_calculation_severity_multiplier_disabled():
    """Confirms chemical dosage multiplier Fv remains strictly neutral (1.00) per regulatory rules."""
    treatment = {
        "base_dose_D0": 0.80,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 1.00,
        "water_dilution_liters_per_acre": 300.0,
        "application_method": "Foliar Spray",
    }
    severity = SeverityResult(
        lesion_to_leaf_ratio=0.15,
        severity_tier="Moderate",
        severity_factor_Fv=1.00,
        leaf_pixels=50000,
        lesion_pixels=7500,
        leaf_detected=True,
        is_reliable=True,
        status_message="Moderate infection",
        estimation_disclaimer="Estimated",
    )

    calc = DosageCalculator.compute_dosage(treatment, severity_result=severity)
    # Chemical dosage multiplier is disabled to prevent phytotoxicity and statutory label violation
    assert calc.severity_factor_Fv == 1.00
    assert calc.raw_calculated_dose == 0.80
    assert calc.final_prescribed_dose == 0.80
    assert calc.is_capped_by_label_max is False
    assert "Disabled" in calc.severity_factor_status


def test_dosage_calculation_high_severity_carrier_water_adjustment():
    """Confirms high severity maintains neutral carrier water volume without unsupported multipliers."""
    treatment = {
        "base_dose_D0": 0.80,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 1.00,
        "water_dilution_liters_per_acre": 300.0,
        "application_method": "Foliar Spray",
    }
    severity = SeverityResult(
        lesion_to_leaf_ratio=0.30,
        severity_tier="High",
        severity_factor_Fv=1.00,
        leaf_pixels=50000,
        lesion_pixels=15000,
        leaf_detected=True,
        is_reliable=True,
        status_message="High infection",
        estimation_disclaimer="Estimated",
    )

    calc = DosageCalculator.compute_dosage(treatment, severity_result=severity)
    # Chemical dose remains uninflated
    assert calc.severity_factor_Fv == 1.00
    assert calc.raw_calculated_dose == 0.80
    assert calc.final_prescribed_dose == 0.80
    # Carrier water volume remains strictly at certified label baseline (300.0 L/acre)
    assert calc.water_dilution_liters_per_acre == 300.0


def test_dosage_calculation_strictly_capped_by_label_maximum():
    """Confirms D_raw is truncated when exceeding statutory D_label_max."""
    # Base dose 1.20 with max cap 1.00
    # Raw = 1.20 > 1.00 -> must cap at 1.00
    treatment = {
        "base_dose_D0": 1.20,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 1.00,
        "water_dilution_liters_per_acre": 300.0,
        "application_method": "Foliar Spray",
    }
    severity = SeverityResult(
        lesion_to_leaf_ratio=0.10,
        severity_tier="Moderate",
        severity_factor_Fv=1.00,
        leaf_pixels=50000,
        lesion_pixels=5000,
        leaf_detected=True,
        is_reliable=True,
        status_message="Moderate infection",
        estimation_disclaimer="Estimated",
    )

    calc = DosageCalculator.compute_dosage(treatment, severity_result=severity)
    assert calc.raw_calculated_dose == 1.20
    assert calc.final_prescribed_dose == 1.00   # Strictly capped at max_legal_dose_cap
    assert calc.is_capped_by_label_max is True


def test_dosage_calculation_unreliable_segmentation_defaults_to_neutral():
    """Confirms Fv defaults to 1.00 if image segmentation is tagged as unreliable."""
    treatment = {
        "base_dose_D0": 0.80,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 1.00,
        "water_dilution_liters_per_acre": 300.0,
        "application_method": "Foliar Spray",
    }
    severity = SeverityResult(
        lesion_to_leaf_ratio=0.40,
        severity_tier="High",
        severity_factor_Fv=1.25,
        leaf_pixels=2000,
        lesion_pixels=800,
        leaf_detected=True,
        is_reliable=False,  # Unreliable segmentation!
        status_message="Noisy background",
        estimation_disclaimer="Estimated",
    )

    calc = DosageCalculator.compute_dosage(treatment, severity_result=severity)
    assert calc.severity_factor_Fv == 1.00  # Reverted to neutral
    assert calc.raw_calculated_dose == 0.80
    assert "Disabled" in calc.severity_factor_status


# ==============================================================================
# 3. Safety Compliance Gate Tests
# ==============================================================================

def test_safety_healthy_plant_requires_no_treatment():
    """Confirms healthy plant diagnosis triggers NO_TREATMENT_NEEDED and suppresses chemicals."""
    safety = SafetyComplianceEngine.evaluate_safety(
        crop="Tomato",
        diagnosed_disease="healthy",
        is_healthy=True,
        diagnostic_confidence=0.98,
        treatment=None,
    )
    assert safety.safety_status == "NO_TREATMENT_NEEDED"
    assert safety.is_safe_to_apply is False
    assert "healthy" in safety.warnings[0].lower()


def test_safety_low_diagnostic_confidence_rejection():
    """Confirms confidence below threshold (0.70) rejects prescription."""
    treatment = {"active_ingredient": "Mancozeb", "verification_status": "VERIFIED"}
    safety = SafetyComplianceEngine.evaluate_safety(
        crop="Tomato",
        diagnosed_disease="Early Blight",
        is_healthy=False,
        diagnostic_confidence=0.58,  # Below 0.70
        treatment=treatment,
    )
    assert safety.is_safe_to_apply is False
    assert safety.safety_status == "REJECTED_LOW_CONFIDENCE"
    assert safety.confidence_check_passed is False
    assert "DIAGNOSTIC CONFIDENCE GATE" in safety.warnings[0]


def test_safety_phi_violation_rejection():
    """Confirms harvest scheduled before PHI expires strictly rejects application."""
    treatment = {
        "active_ingredient": "Tricyclazole",
        "phi_days": 30,  # 30-day PHI
        "verification_status": "VERIFIED",
    }
    # Farmer intends to harvest in 10 days
    safety = SafetyComplianceEngine.evaluate_safety(
        crop="Rice",
        diagnosed_disease="Blast",
        is_healthy=False,
        diagnostic_confidence=0.88,
        treatment=treatment,
        days_to_harvest=10,
    )
    assert safety.is_safe_to_apply is False
    assert safety.safety_status == "REJECTED_PHI_VIOLATION"
    assert safety.phi_check_passed is False
    assert any("CRITICAL PHI VIOLATION" in w for w in safety.warnings)


def test_safety_chemical_incompatibility_rejection():
    """Confirms incompatible tank-mix partner causes rejection."""
    treatment = {
        "active_ingredient": "Mancozeb",
        "phi_days": 14,
        "verification_status": "VERIFIED",
    }
    safety = SafetyComplianceEngine.evaluate_safety(
        crop="Tomato",
        diagnosed_disease="Early Blight",
        is_healthy=False,
        diagnostic_confidence=0.92,
        treatment=treatment,
        co_applied_chemicals=["Azoxystrobin"],  # Incompatible pair
    )
    assert safety.is_safe_to_apply is False
    assert safety.safety_status == "REJECTED_INCOMPATIBILITY"
    assert safety.compatibility_check_passed is False


def test_safety_unverified_demo_record_rejection():
    """Confirms unverified demonstration record is rejected from actionable prescription."""
    treatment = {
        "active_ingredient": "DemoChemical",
        "phi_days": 7,
        "verification_status": "DEMONSTRATION_UNVERIFIED",
    }
    safety = SafetyComplianceEngine.evaluate_safety(
        crop="Tomato",
        diagnosed_disease="Early Blight",
        is_healthy=False,
        diagnostic_confidence=0.90,
        treatment=treatment,
    )
    assert safety.is_safe_to_apply is False
    assert safety.safety_status == "REJECTED_UNVERIFIED"
    assert safety.verification_check_passed is False


# ==============================================================================
# 4. End-to-End Fusion Service Tests
# ==============================================================================

@pytest.mark.anyio
async def test_fusion_service_full_success_verified_treatment():
    """Tests end-to-end fusion producing an approved bounded prescription."""
    mock_soil = MagicMock()
    mock_soil.get_telemetry = AsyncMock(return_value=SoilTelemetryResponse(
        latitude=13.0,
        longitude=77.0,
        telemetry_source="ISRIC_SoilGrids_2.0",
        data_status="live",
        is_fallback=False,
        retrieval_timestamp="2026-11-25T00:00:00Z",
        parameters=SoilTelemetryParameters(pH=6.5, organic_carbon_g_kg=14.0),
        advisory_notice="Modeled estimate",
    ))

    service = FusionService(soil_svc=mock_soil)
    response = await service.fuse_and_recommend(
        crop_name="Tomato",
        crop_stage="Vegetative",
        latitude=13.0,
        longitude=77.0,
        days_to_harvest=25,  # > 14-day PHI
        diagnosed_disease_override="Early Blight",
        diagnostic_confidence_override=0.91,
    )

    assert response.recommendation_available is True
    assert response.status == "SUCCESS"
    assert response.treatment is not None
    assert response.treatment.active_ingredient == "Mancozeb"
    assert response.dosage_breakdown is not None
    assert response.dosage_breakdown.final_prescribed_dose == 0.80
    assert response.safety_assessment.is_safe_to_apply is True
    assert response.telemetry_summary.soil_data_status == "live"


@pytest.mark.anyio
async def test_fusion_service_missing_soil_data_graceful_handling():
    """Confirms missing/unavailable soil data does not crash fusion and sets neutral Fs=1.0."""
    mock_soil = MagicMock()
    mock_soil.get_telemetry = AsyncMock(return_value=SoilTelemetryResponse(
        latitude=0.0,
        longitude=0.0,
        telemetry_source="Unavailable",
        data_status="unavailable",
        is_fallback=True,
        retrieval_timestamp="2026-11-25T00:00:00Z",
        parameters=None,
        advisory_notice="Unavailable",
    ))

    service = FusionService(soil_svc=mock_soil)
    response = await service.fuse_and_recommend(
        crop_name="Potato",
        crop_stage="Vegetative",
        latitude=0.0,
        longitude=0.0,
        days_to_harvest=20,
        diagnosed_disease_override="Late Blight",
        diagnostic_confidence_override=0.88,
    )

    assert response.recommendation_available is True
    assert response.status == "SUCCESS"
    assert response.telemetry_summary.soil_data_status == "unavailable"
    assert response.dosage_breakdown.soil_factor_Fs == 1.00
    assert "Disabled" in response.dosage_breakdown.soil_factor_status


@pytest.mark.anyio
async def test_fusion_service_missing_diagnosis_rejection():
    """Confirms missing diagnosis rejects recommendation with explicit status."""
    service = FusionService()
    response = await service.fuse_and_recommend(
        crop_name="Tomato",
        crop_stage="Vegetative",
        latitude=13.0,
        longitude=77.0,
    )

    assert response.recommendation_available is False
    assert response.status == "DIAGNOSIS_UNAVAILABLE"
    assert response.treatment is None


def test_verified_treatments_comprehensive_citation_audit():
    """Audits all verified treatments to ensure complete statutory and scientific citations."""
    assert len(VERIFIED_TREATMENTS) == 5
    for t in VERIFIED_TREATMENTS:
        assert t["verification_status"] == "VERIFIED"
        assert t["crop"] in ["Tomato", "Potato", "Rice"]
        assert t["disease"] in ["Early Blight", "Late Blight", "Blast"]
        assert len(t["registered_product_name"]) > 0
        assert len(t["official_document"]) > 0
        assert len(t["official_citation_detail"]) > 0
        assert t["statutory_source_url"].startswith("https://ppqs.gov.in")
        assert t["base_dose_D0"] > 0
        assert t["max_legal_dose_cap"] >= t["base_dose_D0"]
        assert t["phi_days"] > 0
        assert len(t["ppe_requirements"]) > 0
        assert len(t["application_method"]) > 0


@pytest.mark.anyio
async def test_fusion_service_returns_traceable_treatment_metadata():
    """Confirms fusion service propagates full official citation and regulatory metadata."""
    mock_soil = MagicMock()
    mock_soil.get_telemetry = AsyncMock(return_value=SoilTelemetryResponse(
        latitude=13.0,
        longitude=77.0,
        telemetry_source="ISRIC_SoilGrids_2.0",
        data_status="live",
        is_fallback=False,
        retrieval_timestamp="2026-11-25T00:00:00Z",
        parameters=SoilTelemetryParameters(pH=6.5),
        advisory_notice="Modeled",
    ))

    service = FusionService(soil_svc=mock_soil)
    response = await service.fuse_and_recommend(
        crop_name="Tomato",
        crop_stage="Vegetative",
        latitude=13.0,
        longitude=77.0,
        days_to_harvest=20,
        diagnosed_disease_override="Early Blight",
        diagnostic_confidence_override=0.95,
    )

    assert response.recommendation_available is True
    assert response.treatment is not None
    assert response.treatment.registered_product_name == "Mancozeb 75% WP"
    assert "CIBRC" in response.treatment.official_document
    assert "Page 42" in response.treatment.official_citation_detail
    assert response.treatment.statutory_source_url == "https://ppqs.gov.in/divisions/cib-rc/major-uses-of-pesticides"

