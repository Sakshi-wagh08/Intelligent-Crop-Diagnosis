import logging
from typing import Dict, Any, Optional, Tuple
from backend.app.schemas.fusion import DosageCalculationBreakdown
from backend.app.schemas.vision import SeverityResult
from backend.app.schemas.soil import SoilTelemetryResponse

logger = logging.getLogger(__name__)


class DosageCalculator:
    """Calculates bounded agricultural chemical dosages adhering strictly to regulatory labels.

    Implements:
        D = min(D0 * Fs * Fv, D_label_max)

    Agronomic Governance:
    - Base dosage D0 is derived strictly from verified agricultural extension packages-of-practices.
    - Soil factor Fs is set to neutral (1.00) for foliar sprays or when soil data is unavailable.
    - Severity factor Fv is bounded by foliar canopy tiers and reverts to 1.00 if segmentation is unreliable.
    - Final dosage D is strictly capped at D_label_max to eliminate any legal or phytotoxic risk.
    """

    @classmethod
    def compute_dosage(
        cls,
        treatment: Dict[str, Any],
        severity_result: Optional[SeverityResult] = None,
        soil_result: Optional[SoilTelemetryResponse] = None,
    ) -> DosageCalculationBreakdown:
        """Computes the bounded dosage with full mathematical audit trail."""
        base_dose_D0 = float(treatment["base_dose_D0"])
        dose_unit = treatment.get("dose_unit", "kg/acre")
        max_label_dose_cap = float(treatment["max_legal_dose_cap"])
        base_water = float(treatment.get("water_dilution_liters_per_acre", 200.0))
        application_method = treatment.get("application_method", "Foliar Spray")

        # 1. Determine Severity Factor Fv
        # AGRONOMIC REGULATORY COMPLIANCE:
        # Official CIBRC/EPA/FAO pesticide product labels strictly specify active ingredient
        # dosage rates per unit area. Artificially increasing pesticide chemical dosage (e.g., * 1.05 or * 1.15)
        # based on foliar symptom severity is NOT authorized by certified product labels, risks foliar
        # phytotoxicity, accelerates pathogen resistance, and violates statutory pesticide regulations.
        # Consequently, chemical dosage multiplier Fv is strictly maintained at neutral (1.00).
        # Foliar canopy adjustments under severe infection are confined to spray carrier water volume.
        Fv = 1.00
        Fv_status = "Disabled (Pesticide chemical dosage multipliers based on severity are prohibited by official label claims and statutory regulations; neutral Fv = 1.00 applied)"

        # 2. Determine Soil Factor Fs
        # Crucial agronomic rule: for foliar sprays, chemical uptake occurs via leaf cuticle,
        # so soil matrix does NOT alter foliar pesticide dosage.
        Fs = 1.00
        Fs_status = "Disabled (Foliar application: uptake independent of soil matrix)"

        if "foliar" not in application_method.lower():
            if soil_result is None or soil_result.data_status == "unavailable" or not soil_result.parameters:
                Fs = 1.00
                Fs_status = "Disabled (Soil telemetry unavailable; neutral 1.00 applied)"
            else:
                # Soil-applied treatment with verified data: explicit auditable rules from pH, SOC, N, texture
                params = soil_result.parameters
                reasons = []
                fs_calc = 1.00

                soc = params.organic_carbon_g_kg
                nitrogen = params.nitrogen_g_kg
                sand = params.sand_fraction_percent
                ph = params.pH

                # Organic Carbon / Nitrogen Reserve Factor
                if (soc is not None and soc < 5.0) or (nitrogen is not None and nitrogen < 1.0):
                    fs_calc *= 1.15
                    reasons.append("low soil organic carbon/nitrogen (+15%)")
                elif (soc is not None and soc > 12.0) or (nitrogen is not None and nitrogen > 2.5):
                    fs_calc *= 0.85
                    reasons.append("high soil organic carbon/nitrogen (-15%)")
                else:
                    reasons.append("moderate soil carbon/nitrogen (1.00)")

                # Sandy soil leaching guard (split smaller single dose)
                if sand is not None and sand >= 65.0:
                    fs_calc *= 0.90
                    reasons.append("sandy soil leaching guard (-10%, split doses recommended)")

                # pH advisory note
                if ph is not None and ph < 5.5:
                    reasons.append(f"acidic pH {ph:.1f} (consider agricultural lime)")
                elif ph is not None and ph > 8.0:
                    reasons.append(f"alkaline pH {ph:.1f} (split application recommended)")

                # Bound Fs safely within [0.75, 1.20]
                Fs = round(max(0.75, min(1.20, fs_calc)), 2)
                Fs_status = f"Active ({soil_result.data_status} soil: {', '.join(reasons)})"

        # 3. Calculate Raw and Bounded Dosage
        raw_dose = round(base_dose_D0 * Fs * Fv, 3)

        # Enforce statutory label ceiling D <= D_label_max
        is_capped = raw_dose > max_label_dose_cap
        final_dose = min(raw_dose, max_label_dose_cap)

        # Carrier water volume remains strictly at the certified package-of-practices baseline.
        # Unsupported severity-based water volume multipliers are removed to adhere to verified label claims.
        prescribed_water = base_water

        return DosageCalculationBreakdown(
            base_dose_D0=round(base_dose_D0, 3),
            dose_unit=dose_unit,
            soil_factor_Fs=round(Fs, 2),
            soil_factor_status=Fs_status,
            severity_factor_Fv=round(Fv, 2),
            severity_factor_status=Fv_status,
            raw_calculated_dose=round(raw_dose, 3),
            max_label_dose_cap=round(max_label_dose_cap, 3),
            final_prescribed_dose=round(final_dose, 3),
            water_dilution_liters_per_acre=prescribed_water,
            is_capped_by_label_max=is_capped,
        )
