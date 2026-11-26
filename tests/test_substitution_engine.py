import pytest
from backend.app.substitution.engine import (
    ProductSubstitutionEngine,
    FOLIAR_FORMULATION_TYPES,
    NON_FOLIAR_FORMULATION_TYPES,
)
from backend.app.substitution.ranking import MerchantProductRanker
from backend.app.schemas.substitution import RankingWeights
from backend.app.substitution.exceptions import (
    ActiveIngredientMismatchError,
    IncompatibleConcentrationUnitError,
    IncompatibleFormulationError,
    UnregisteredProductError,
    CropDiseaseMismatchError,
    InvalidDosageError,
)


# ==============================================================================
# 1. Chemical Active Ingredient Substitution Calculations (Qs = Qr * (Cr / Cs))
# ==============================================================================

def test_substitution_exact_concentration_ratio():
    """Confirms Qs = Qr when substitute formulation concentration Cs equals reference Cr."""
    # Reference Mancozeb 75% WP @ 0.80 kg/acre
    # Substitute Mancozeb 75% WP (Cs = 75.0%)
    sub_dose, ratio = ProductSubstitutionEngine.calculate_substitute_dose(
        reference_dose_Qr=0.80,
        reference_concentration_Cr=75.0,
        substitute_concentration_Cs=75.0,
    )
    assert ratio == 1.00
    assert sub_dose == 0.80


def test_substitution_higher_concentration_ratio():
    """Confirms Qs decreases when substitute concentration Cs is higher (Cs = 80% vs Cr = 75%)."""
    # Qs = 0.80 * (75 / 80) = 0.80 * 0.9375 = 0.75 kg/acre
    sub_dose, ratio = ProductSubstitutionEngine.calculate_substitute_dose(
        reference_dose_Qr=0.80,
        reference_concentration_Cr=75.0,
        substitute_concentration_Cs=80.0,
    )
    assert ratio == 0.9375
    assert sub_dose == 0.75


def test_substitution_lower_concentration_ratio():
    """Confirms Qs increases when substitute concentration Cs is lower (Cs = 50% vs Cr = 75%)."""
    # Qs = 0.80 * (75 / 50) = 0.80 * 1.5 = 1.20 kg/acre
    sub_dose, ratio = ProductSubstitutionEngine.calculate_substitute_dose(
        reference_dose_Qr=0.80,
        reference_concentration_Cr=75.0,
        substitute_concentration_Cs=50.0,
    )
    assert ratio == 1.50
    assert sub_dose == 1.20


def test_substitution_concentration_unit_conversion():
    """Confirms unit conversion between g/kg and % (750 g/kg == 75.0%)."""
    # Reference Cr in % (75.0%), Substitute Cs in g/kg (750 g/kg)
    sub_dose, ratio = ProductSubstitutionEngine.calculate_substitute_dose(
        reference_dose_Qr=0.80,
        reference_concentration_Cr=75.0,
        substitute_concentration_Cs=750.0,
        reference_unit_Cr="%",
        substitute_unit_Cs="g/kg",
    )
    assert ratio == 1.00
    assert sub_dose == 0.80


def test_substitution_incompatible_concentration_unit_raises_error():
    """Confirms unknown or incompatible concentration units raise IncompatibleConcentrationUnitError."""
    with pytest.raises(IncompatibleConcentrationUnitError):
        ProductSubstitutionEngine.calculate_substitute_dose(
            reference_dose_Qr=0.80,
            reference_concentration_Cr=75.0,
            substitute_concentration_Cs=100.0,
            reference_unit_Cr="%",
            substitute_unit_Cs="incompatible_unit",
        )


def test_substitution_invalid_negative_or_zero_dosage():
    """Confirms zero or negative dosages raise InvalidDosageError."""
    with pytest.raises(InvalidDosageError):
        ProductSubstitutionEngine.calculate_substitute_dose(
            reference_dose_Qr=-0.5,
            reference_concentration_Cr=75.0,
            substitute_concentration_Cs=75.0,
        )

    with pytest.raises(InvalidDosageError):
        ProductSubstitutionEngine.calculate_substitute_dose(
            reference_dose_Qr=0.80,
            reference_concentration_Cr=75.0,
            substitute_concentration_Cs=-10.0,
        )


# ==============================================================================
# 2. Package Size Parsing & Retail Pack Requirement Calculation
# ==============================================================================

def test_package_size_parsing():
    """Validates parsing of common commercial agrochemical package sizes."""
    assert ProductSubstitutionEngine.parse_package_size("1 kg") == (1.0, "kg")
    assert ProductSubstitutionEngine.parse_package_size("500 g") == (0.5, "kg")
    assert ProductSubstitutionEngine.parse_package_size("250 g") == (0.25, "kg")
    assert ProductSubstitutionEngine.parse_package_size("5 kg") == (5.0, "kg")
    assert ProductSubstitutionEngine.parse_package_size("1 L") == (1.0, "L")
    assert ProductSubstitutionEngine.parse_package_size("500 mL") == (0.5, "L")
    assert ProductSubstitutionEngine.parse_package_size("250 mL") == (0.25, "L")
    assert ProductSubstitutionEngine.parse_package_size("100 ml") == (0.1, "L")


def test_calculate_required_packages():
    """Validates computation of total product required and package count ceil rounding."""
    # 0.75 kg/acre on 2.0 acres = 1.50 kg total
    # With 1 kg packs -> ceil(1.50 / 1.0) = 2 packs
    total_qty, packs, desc = ProductSubstitutionEngine.calculate_required_packages(
        substitute_dose_Qs=0.75,
        field_area_acres=2.0,
        package_size_str="1 kg",
    )
    assert total_qty == 1.50
    assert packs == 2
    assert "1.0 kg" in desc

    # 0.20 L/acre on 1.0 acre = 0.20 L total
    # With 500 mL packs (0.5 L) -> ceil(0.20 / 0.5) = 1 pack
    total_qty_liq, packs_liq, desc_liq = ProductSubstitutionEngine.calculate_required_packages(
        substitute_dose_Qs=0.20,
        field_area_acres=1.0,
        package_size_str="500 mL",
        dose_unit="L/acre",
    )
    assert total_qty_liq == 0.20
    assert packs_liq == 1


# ==============================================================================
# 3. Product Eligibility & Regulatory Screening Rules
# ==============================================================================

def test_eligibility_active_ingredient_match():
    """Validates that candidate with identical active ingredient passes rule 1."""
    is_ok, reason = ProductSubstitutionEngine.evaluate_product_eligibility(
        product_brand="DemoIndo Mancozeb 75 WP",
        product_active_ingredient="Mancozeb",
        product_formulation="WP",
        is_legally_registered=True,
        registration_number="CIB-DEMO-2026-001",
        registered_crops="Tomato, Potato",
        registered_diseases="Early Blight, Late Blight",
        required_active_ingredient="Mancozeb",
        target_crop="Tomato",
        target_disease="Early Blight",
        prescribed_application_method="Foliar Spray",
    )
    assert is_ok is True
    assert "Eligible" in reason


def test_eligibility_active_ingredient_mismatch_rejection():
    """Confirms rejection when active ingredients do not match."""
    is_ok, reason = ProductSubstitutionEngine.evaluate_product_eligibility(
        product_brand="DemoStrobin 23 SC",
        product_active_ingredient="Azoxystrobin",
        product_formulation="SC",
        is_legally_registered=True,
        registration_number="CIB-DEMO-2026-004",
        registered_crops="Tomato",
        registered_diseases="Early Blight",
        required_active_ingredient="Mancozeb",  # Mismatch!
        target_crop="Tomato",
        target_disease="Early Blight",
    )
    assert is_ok is False
    assert "Active ingredient mismatch" in reason


def test_eligibility_unregistered_product_rejection():
    """Confirms rejection when candidate lacks legal statutory registration."""
    is_ok, reason = ProductSubstitutionEngine.evaluate_product_eligibility(
        product_brand="DemoBootleg Mancozeb 75 WP",
        product_active_ingredient="Mancozeb",
        product_formulation="WP",
        is_legally_registered=False,  # Unregistered!
        registration_number="CIB-DEMO-EXPIRED",
        registered_crops="Tomato",
        registered_diseases="Early Blight",
        required_active_ingredient="Mancozeb",
        target_crop="Tomato",
        target_disease="Early Blight",
    )
    assert is_ok is False
    assert "lacks valid statutory CIBRC registration" in reason


def test_eligibility_crop_mismatch_rejection():
    """Confirms rejection when product is not registered for target crop."""
    # Registered for Cotton only, farmer is treating Tomato
    is_ok, reason = ProductSubstitutionEngine.evaluate_product_eligibility(
        product_brand="DemoCotton Mancozeb 75 WP",
        product_active_ingredient="Mancozeb",
        product_formulation="WP",
        is_legally_registered=True,
        registration_number="CIB-DEMO-2026-007",
        registered_crops="Cotton",  # Cotton only!
        registered_diseases="Leaf Spot",
        required_active_ingredient="Mancozeb",
        target_crop="Tomato",  # Target is Tomato
        target_disease="Early Blight",
    )
    assert is_ok is False
    assert "Not officially registered for crop 'Tomato'" in reason


def test_eligibility_disease_mismatch_rejection():
    """Confirms rejection when product is registered for crop but not target disease."""
    is_ok, reason = ProductSubstitutionEngine.evaluate_product_eligibility(
        product_brand="DemoDamping Mancozeb 75 WP",
        product_active_ingredient="Mancozeb",
        product_formulation="WP",
        is_legally_registered=True,
        registration_number="CIB-DEMO-2026-010",
        registered_crops="Tomato",
        registered_diseases="Damping Off",  # Damping Off only, not Early Blight
        required_active_ingredient="Mancozeb",
        target_crop="Tomato",
        target_disease="Early Blight",
    )
    assert is_ok is False
    assert "disease 'Early Blight'" in reason


def test_eligibility_incompatible_formulation_rejection():
    """Confirms non-foliar formulation (Granules) is rejected when foliar spray is required."""
    is_ok, reason = ProductSubstitutionEngine.evaluate_product_eligibility(
        product_brand="DemoGranule Mancozeb 5 GR",
        product_active_ingredient="Mancozeb",
        product_formulation="GR",  # Granules!
        is_legally_registered=True,
        registration_number="CIB-DEMO-2026-008",
        registered_crops="Tomato",
        registered_diseases="Early Blight",
        required_active_ingredient="Mancozeb",
        target_crop="Tomato",
        target_disease="Early Blight",
        prescribed_application_method="Foliar Spray",
    )
    assert is_ok is False
    assert "Incompatible formulation 'GR'" in reason


# ==============================================================================
# 4. Multi-Factor Dealer & Product Ranking Engine
# ==============================================================================

def test_ranker_factor_normalization():
    """Validates price, distance, and stock normalization ranges [0.0 - 1.0]."""
    # Price: min=350, max=500. Candidate price=350 -> 1.0 (cheapest)
    assert MerchantProductRanker.normalize_price(350.0, 350.0, 500.0) == 1.00
    # Candidate price=500 -> 0.0 (most expensive)
    assert MerchantProductRanker.normalize_price(500.0, 350.0, 500.0) == 0.00
    # Candidate price=425 -> 0.50 (median)
    assert MerchantProductRanker.normalize_price(425.0, 350.0, 500.0) == 0.50

    # Distance: radius=25 km. Distance=0 km -> 1.0 (origin)
    assert MerchantProductRanker.normalize_distance(0.0, 25.0) == 1.00
    # Distance=25 km -> 0.0 (boundary)
    assert MerchantProductRanker.normalize_distance(25.0, 25.0) == 0.00
    # Distance=12.5 km -> 0.50
    assert MerchantProductRanker.normalize_distance(12.5, 25.0) == 0.50

    # Stock: packs_needed=2. In stock=2 -> 1.0
    assert MerchantProductRanker.normalize_stock(2, 2) == 1.00
    # In stock=5 -> 1.0
    assert MerchantProductRanker.normalize_stock(5, 2) == 1.00
    # In stock=1 -> 0.50
    assert MerchantProductRanker.normalize_stock(1, 2) == 0.50
    # In stock=0 -> 0.0
    assert MerchantProductRanker.normalize_stock(0, 2) == 0.00


def test_ranker_composite_weighted_score():
    """Validates composite score computation using configurable weights."""
    weights = RankingWeights(price=0.40, distance=0.35, stock=0.25)
    # Perfect candidate: 1.0 across all factors -> composite = 1.0
    score_perf = MerchantProductRanker.compute_composite_score(1.0, 1.0, 1.0, weights)
    assert score_perf == 1.00

    # Mid candidate: price=1.0, distance=0.5, stock=1.0
    # Score = (0.40*1.0 + 0.35*0.5 + 0.25*1.0) / 1.00 = 0.40 + 0.175 + 0.25 = 0.825
    score_mid = MerchantProductRanker.compute_composite_score(1.0, 0.5, 1.0, weights)
    assert score_mid == 0.825


def test_ranker_explanation_generation():
    """Validates human-readable explainability output for recommended rankings."""
    exp = MerchantProductRanker.generate_explanation(
        rank=1,
        brand_name="DemoIndo Mancozeb 75 WP",
        merchant_name="Kisan Seva Kendra",
        total_cost=420.0,
        distance_km=5.2,
        stock_qty=25,
        packages_needed=1,
        price_score=0.90,
        distance_score=0.85,
        stock_score=1.0,
    )
    assert "Ranked #1" in exp
    assert "highly competitive price" in exp
    assert "very close proximity" in exp
    assert "full inventory availability" in exp


# ==============================================================================
# 5. Scientific Concentration Basis & Physical Mass-Volume Unit Tests
# ==============================================================================

def test_substitution_distinguishes_mass_and_volume_bases():
    """Confirms % w/w to g/kg and % w/v to g/L conversions succeed within same basis."""
    # Mass basis: 75% w/w to 750 g/kg -> ratio = 1.0
    sub_dose, ratio = ProductSubstitutionEngine.calculate_substitute_dose(
        reference_dose_Qr=0.80,
        reference_concentration_Cr=75.0,
        substitute_concentration_Cs=750.0,
        reference_unit_Cr="% w/w",
        substitute_unit_Cs="g/kg",
    )
    assert ratio == 1.00
    assert sub_dose == 0.80

    # Volume basis: 23% w/v to 230 g/L -> ratio = 1.0
    sub_dose_v, ratio_v = ProductSubstitutionEngine.calculate_substitute_dose(
        reference_dose_Qr=0.20,
        reference_concentration_Cr=23.0,
        substitute_concentration_Cs=230.0,
        reference_unit_Cr="% w/v",
        substitute_unit_Cs="g/L",
    )
    assert ratio_v == 1.00
    assert sub_dose_v == 0.20


def test_substitution_cross_basis_without_density_rejected():
    """Confirms cross-converting between mass (% w/w) and volume (% w/v) without density raises error."""
    with pytest.raises(IncompatibleConcentrationUnitError) as exc_info:
        ProductSubstitutionEngine.calculate_substitute_dose(
            reference_dose_Qr=0.80,
            reference_concentration_Cr=75.0,
            substitute_concentration_Cs=23.0,
            reference_unit_Cr="% w/w",   # Mass basis
            substitute_unit_Cs="% w/v",  # Volume basis
            substitute_density_g_ml=None,  # No density!
        )
    assert "requires verified product density" in str(exc_info.value)


def test_substitution_cross_basis_with_density_succeeds():
    """Confirms cross-converting between % w/w and % w/v succeeds when valid formulation density is provided."""
    # Reference: 75% w/w. Substitute: 90% w/v with density = 1.20 g/mL
    # Substitute % w/w = 90 / 1.20 = 75% w/w.
    # Ratio = 75 / 75 = 1.0. Qs = 0.80 * 1.0 = 0.80.
    sub_dose, ratio = ProductSubstitutionEngine.calculate_substitute_dose(
        reference_dose_Qr=0.80,
        reference_concentration_Cr=75.0,
        substitute_concentration_Cs=90.0,
        reference_unit_Cr="% w/w",
        substitute_unit_Cs="% w/v",
        substitute_density_g_ml=1.20,
    )
    assert ratio == 1.00
    assert sub_dose == 0.80


def test_package_size_mass_volume_mismatch_without_density_rejected():
    """Confirms dosing in kg/acre with pack size in mL/L without density raises error."""
    with pytest.raises(IncompatibleConcentrationUnitError) as exc_info:
        ProductSubstitutionEngine.calculate_required_packages(
            substitute_dose_Qs=0.80,
            field_area_acres=1.0,
            package_size_str="500 mL",  # Volume pack!
            dose_unit="kg/acre",        # Mass dose!
            product_density_kg_per_l=None,
        )
    assert "Physical unit mismatch" in str(exc_info.value)


def test_package_size_mass_volume_with_density_succeeds():
    """Confirms dosing in kg/acre with volume pack succeeds when density is provided."""
    # 0.80 kg needed. 1 L pack with density = 1.25 kg/L -> 1 pack holds 1.25 kg.
    # ceil(0.80 / 1.25) = 1 pack.
    total_qty, packs, desc = ProductSubstitutionEngine.calculate_required_packages(
        substitute_dose_Qs=0.80,
        field_area_acres=1.0,
        package_size_str="1 L",
        dose_unit="kg/acre",
        product_density_kg_per_l=1.25,
    )
    assert total_qty == 0.80
    assert packs == 1


# ==============================================================================
# 6. Ranking Edge Cases: Zero/Missing Stock, Zero/Equal Prices, Zero Radius
# ==============================================================================

def test_ranking_edge_cases():
    """Validates behavior for missing stock, zero stock, zero price, equal prices, and zero radius."""
    # Missing stock (None) -> 0.0
    assert MerchantProductRanker.normalize_stock(None, 2) == 0.0
    # Negative stock -> 0.0
    assert MerchantProductRanker.normalize_stock(-5, 2) == 0.0
    # Zero stock -> 0.0
    assert MerchantProductRanker.normalize_stock(0, 2) == 0.0

    # Zero or negative price -> 0.0
    assert MerchantProductRanker.normalize_price(0.0, 300.0, 500.0) == 0.0
    assert MerchantProductRanker.normalize_price(-10.0, 300.0, 500.0) == 0.0
    assert MerchantProductRanker.normalize_price(None, 300.0, 500.0) == 0.0

    # Equal prices (all dealers charge same price) -> 1.0 (no penalty)
    assert MerchantProductRanker.normalize_price(420.0, 420.0, 420.0) == 1.0

    # Zero search radius -> 1.0 (origin)
    assert MerchantProductRanker.normalize_distance(0.0, 0.0) == 1.0
    # Negative distance -> 1.0
    assert MerchantProductRanker.normalize_distance(-1.0, 25.0) == 1.0

