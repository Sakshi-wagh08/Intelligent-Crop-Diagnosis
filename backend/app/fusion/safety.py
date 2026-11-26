import logging
from typing import Dict, List, Optional, Tuple, Any
from backend.app.schemas.fusion import SafetyAssessment
from backend.app.fusion.knowledge_base import AgronomicKnowledgeBase

logger = logging.getLogger(__name__)

DEFAULT_CONFIDENCE_THRESHOLD = 0.70


class SafetyComplianceEngine:
    """Enforces regulatory compliance, PHI checks, PPE directives, and chemical safety."""

    @classmethod
    def evaluate_safety(
        cls,
        crop: str,
        diagnosed_disease: str,
        is_healthy: bool,
        diagnostic_confidence: float,
        treatment: Optional[Dict[str, Any]],
        days_to_harvest: Optional[int] = None,
        co_applied_chemicals: Optional[List[str]] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> SafetyAssessment:
        """Conducts an exhaustive safety evaluation across all regulatory and agronomic dimensions."""
        warnings: List[str] = []
        protective_equipment: List[str] = []
        is_safe = True
        status = "APPROVED"

        # Case 1: Healthy plant - no chemical needed
        if is_healthy:
            return SafetyAssessment(
                is_safe_to_apply=False,
                safety_status="NO_TREATMENT_NEEDED",
                confidence_check_passed=True,
                phi_check_passed=True,
                compatibility_check_passed=True,
                verification_check_passed=True,
                warnings=["Plant is healthy. Chemical fungicides/pesticides are NOT recommended."],
                protective_equipment=[],
                environmental_precautions="Maintain ecological balance and beneficial insect populations.",
            )

        # Check 1: Diagnostic Confidence Safety Gate
        conf_passed = diagnostic_confidence >= confidence_threshold
        if not conf_passed:
            is_safe = False
            status = "REJECTED_LOW_CONFIDENCE"
            msg = (
                f"DIAGNOSTIC CONFIDENCE GATE: Vision confidence ({diagnostic_confidence * 100:.1f}%) "
                f"is below the minimum safety threshold ({confidence_threshold * 100:.1f}%). "
                "Chemical dosage recommendation withheld to prevent chemical misapplication."
            )
            warnings.append(msg)

        # Check 2: Treatment Availability
        if not treatment:
            is_safe = False
            status = status if not conf_passed else "REJECTED_NO_TREATMENT_FOUND"
            warnings.append(f"No registered agricultural treatment guideline available for {crop} infected with {diagnosed_disease}.")
            return SafetyAssessment(
                is_safe_to_apply=False,
                safety_status=status,
                confidence_check_passed=conf_passed,
                phi_check_passed=True,
                compatibility_check_passed=True,
                verification_check_passed=False,
                warnings=warnings,
                protective_equipment=[],
                environmental_precautions="Consult local government agricultural extension officer for diagnostic verification.",
            )

        # Check 3: Scientific Verification Status
        v_status = treatment.get("verification_status", "DEMONSTRATION_UNVERIFIED")
        v_passed = (v_status == "VERIFIED")
        if not v_passed:
            is_safe = False
            if status == "APPROVED":
                status = "REJECTED_UNVERIFIED"
            warnings.append(
                f"VERIFICATION WARNING: Treatment guideline is classified as '{v_status}'. "
                "Field chemical prescription is prohibited for unverified research demonstration records."
            )

        # Check 4: Pre-Harvest Interval (PHI) Compliance
        phi_days = treatment.get("phi_days", 0)
        phi_passed = True
        if days_to_harvest is not None:
            if days_to_harvest < phi_days:
                is_safe = False
                phi_passed = False
                if status == "APPROVED":
                    status = "REJECTED_PHI_VIOLATION"
                warnings.append(
                    f"CRITICAL PHI VIOLATION: Crop harvest is scheduled in {days_to_harvest} days, but "
                    f"'{treatment.get('active_ingredient')}' requires a statutory Pre-Harvest Interval of {phi_days} days. "
                    "Application would cause hazardous illegal chemical residue on harvested produce."
                )
            else:
                warnings.append(
                    f"PHI Cleared: Harvest scheduled in {days_to_harvest} days satisfies minimum {phi_days}-day PHI."
                )

        # Check 5: Tank-Mix Chemical Incompatibilities
        co_applied = co_applied_chemicals or []
        ai_name = treatment.get("active_ingredient", "")
        incomp_warnings = AgronomicKnowledgeBase.check_incompatibility(ai_name, co_applied)
        compat_passed = len(incomp_warnings) == 0
        if not compat_passed:
            is_safe = False
            if status == "APPROVED":
                status = "REJECTED_INCOMPATIBILITY"
            warnings.extend(incomp_warnings)

        # Parse PPE requirements
        raw_ppe = treatment.get("ppe_requirements", "")
        if raw_ppe:
            protective_equipment = [item.strip() for item in raw_ppe.split(",") if item.strip()]

        # Environmental & Label Precautions
        label_restrictions = treatment.get("label_restrictions", "")
        env_precautions = (
            f"{label_restrictions} "
            "Do not spray during peak bee foraging hours (midday). Avoid drift into aquatic habitats or neighboring crops. "
            "Clean spray equipment thoroughly after application."
        ).strip()

        return SafetyAssessment(
            is_safe_to_apply=is_safe,
            safety_status=status,
            confidence_check_passed=conf_passed,
            phi_check_passed=phi_passed,
            compatibility_check_passed=compat_passed,
            verification_check_passed=v_passed,
            warnings=warnings,
            protective_equipment=protective_equipment,
            environmental_precautions=env_precautions,
        )
