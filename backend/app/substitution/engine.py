import re
import math
import logging
from typing import Tuple, Optional, Dict, Any, List

from backend.app.substitution.exceptions import (
    ActiveIngredientMismatchError,
    IncompatibleConcentrationUnitError,
    IncompatibleFormulationError,
    UnregisteredProductError,
    CropDiseaseMismatchError,
    InvalidDosageError,
)

logger = logging.getLogger(__name__)

# Validated formulation classifications
FOLIAR_FORMULATION_TYPES = {
    "WP",   # Wettable Powder
    "WG",   # Water Dispersible Granules
    "WDG",  # Water Dispersible Granules
    "SC",   # Suspension Concentrate
    "EC",   # Emulsifiable Concentrate
    "SL",   # Soluble Liquid Concentrate
    "SP",   # Soluble Powder
    "FS",   # Flowable Concentrate for Seed / Foliar
    "CS",   # Capsule Suspension
}

NON_FOLIAR_FORMULATION_TYPES = {
    "GR": "Granules (Soil Broadcast / Soil Incorporation)",
    "G": "Granules (Soil Broadcast)",
    "DP": "Dusting Powder (Dry Foliar Dusting - Not Spray Dilution)",
    "DS": "Powder for Dry Seed Treatment",
    "WS": "Water Dispersible Powder for Slurry Seed Treatment",
    "CG": "Encapsulated Granules",
}


class ConcentrationBasis:
    MASS = "MASS"      # % w/w, g/kg (mass active ingredient per mass formulation)
    VOLUME = "VOLUME"  # % w/v, g/L (mass active ingredient per volume formulation)


class ProductSubstitutionEngine:
    """Core mathematical and agronomic validation engine for chemical active ingredient substitution.

    Implements:
        Qs = Qr * (Cr / Cs)

    Agronomic Governance & Physical Basis:
    - Products are NOT interchangeable merely by sharing the same active ingredient.
    - Rigorously distinguishes mass-basis (% w/w, g/kg) and volume-basis (% w/v, g/L).
    - Prohibits assuming 1% equals both 10 g/kg and 10 g/L indiscriminately.
    - Prohibits cross-basis mass-to-volume conversion without verified formulation density.
    - Prohibits invalid kg-to-litre package conversions without density information.
    - Enforces statutory registration and crop/disease label authorization.
    """

    @classmethod
    def determine_concentration_basis(
        cls,
        unit: str,
        formulation_type: Optional[str] = None,
        dose_unit: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Determines the concentration basis (MASS or VOLUME) and normalized unit label.

        Returns:
            Tuple of (normalized_unit_str, basis: ConcentrationBasis.MASS | ConcentrationBasis.VOLUME)
        """
        clean_unit = unit.strip().lower()

        # Explicit mass-basis units
        if clean_unit in ["% w/w", "%(w/w)", "w/w", "% w-w", "g/kg", "gm/kg", "g/kilo", "mg/kg"]:
            return clean_unit, ConcentrationBasis.MASS

        # Explicit volume-basis units
        if clean_unit in ["% w/v", "%(w/v)", "w/v", "% w-v", "g/l", "g/liter", "g/litre", "gm/l", "mg/l"]:
            return clean_unit, ConcentrationBasis.VOLUME

        # Generic percentage "%": determine basis from formulation or dose unit
        if clean_unit in ["%", "percent", "pct"]:
            if formulation_type:
                f_clean = formulation_type.strip().upper()
                if f_clean in ["WP", "WG", "WDG", "SP", "DP", "GR", "G", "DS", "WS"]:
                    return "% w/w", ConcentrationBasis.MASS
                if f_clean in ["SC", "EC", "SL", "CS", "FS"]:
                    return "% w/v", ConcentrationBasis.VOLUME

            if dose_unit:
                d_clean = dose_unit.strip().lower()
                if "kg" in d_clean or "g" in d_clean:
                    return "% w/w", ConcentrationBasis.MASS
                if "l" in d_clean or "ml" in d_clean:
                    return "% w/v", ConcentrationBasis.VOLUME

            # Default to MASS if unspecified
            return "% w/w", ConcentrationBasis.MASS

        raise IncompatibleConcentrationUnitError(
            f"Unrecognized concentration unit '{unit}'. Supported units: '% w/w', '% w/v', 'g/kg', 'g/L', '%'."
        )

    @classmethod
    def normalize_concentration(
        cls,
        concentration: float,
        unit: str,
        formulation_type: Optional[str] = None,
        dose_unit: Optional[str] = None,
    ) -> Tuple[float, str]:
        """Normalizes concentration to either % w/w (for MASS basis) or % w/v (for VOLUME basis).

        Returns:
            Tuple of (normalized_percentage, basis: ConcentrationBasis.MASS | ConcentrationBasis.VOLUME)
        """
        if concentration <= 0.0:
            raise InvalidDosageError(f"Concentration must be strictly positive, got {concentration}")

        clean_unit, basis = cls.determine_concentration_basis(unit, formulation_type, dose_unit)

        if basis == ConcentrationBasis.MASS:
            # 1% w/w = 10 g/kg (mass basis)
            if clean_unit in ["g/kg", "gm/kg", "g/kilo"]:
                return float(concentration) / 10.0, basis
            elif clean_unit == "mg/kg":
                return float(concentration) / 10000.0, basis
            else:
                return float(concentration), basis

        elif basis == ConcentrationBasis.VOLUME:
            # 1% w/v = 10 g/L (volume basis)
            if clean_unit in ["g/l", "g/liter", "g/litre", "gm/l"]:
                return float(concentration) / 10.0, basis
            elif clean_unit == "mg/l":
                return float(concentration) / 10000.0, basis
            else:
                return float(concentration), basis

        raise IncompatibleConcentrationUnitError(f"Unable to normalize concentration unit '{unit}'.")

    @classmethod
    def calculate_substitute_dose(
        cls,
        reference_dose_Qr: float,
        reference_concentration_Cr: float,
        substitute_concentration_Cs: float,
        reference_unit_Cr: str = "%",
        substitute_unit_Cs: str = "%",
        reference_formulation: Optional[str] = None,
        substitute_formulation: Optional[str] = None,
        reference_dose_unit: Optional[str] = None,
        substitute_density_g_ml: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Calculates equivalent substitute dosage Qs = Qr * (Cr / Cs) with strict basis verification.

        Returns:
            Tuple of (substitute_dose_Qs, concentration_ratio)
        """
        if reference_dose_Qr <= 0.0:
            raise InvalidDosageError(f"Reference dosage Qr must be strictly positive, got {reference_dose_Qr}")

        cr_norm, basis_cr = cls.normalize_concentration(
            reference_concentration_Cr, reference_unit_Cr, reference_formulation, reference_dose_unit
        )
        cs_norm, basis_cs = cls.normalize_concentration(
            substitute_concentration_Cs, substitute_unit_Cs, substitute_formulation, reference_dose_unit
        )

        if cs_norm <= 0.0:
            raise InvalidDosageError(f"Normalized substitute concentration Cs must be > 0, got {cs_norm}")

        # Check cross-basis consistency
        if basis_cr != basis_cs:
            # Cross-basis conversion requires formulation density
            if substitute_density_g_ml is None or substitute_density_g_ml <= 0.0:
                raise IncompatibleConcentrationUnitError(
                    f"Cross-basis concentration conversion error: Reference concentration is {basis_cr}-basis "
                    f"('{reference_unit_Cr}') while substitute is {basis_cs}-basis ('{substitute_unit_Cs}'). "
                    "Cross-converting between mass and volume bases requires verified product density (g/mL), "
                    "which is unavailable."
                )
            # Apply density conversion:
            # If Cr is MASS (% w/w) and Cs is VOLUME (% w/v):
            # Cs (% w/v) = Cs (% w/w) * density => Cs (% w/w) = Cs (% w/v) / density
            if basis_cr == ConcentrationBasis.MASS and basis_cs == ConcentrationBasis.VOLUME:
                cs_norm = cs_norm / substitute_density_g_ml
            elif basis_cr == ConcentrationBasis.VOLUME and basis_cs == ConcentrationBasis.MASS:
                cs_norm = cs_norm * substitute_density_g_ml

        ratio = cr_norm / cs_norm
        substitute_dose_Qs = round(reference_dose_Qr * ratio, 4)

        return substitute_dose_Qs, round(ratio, 4)

    @classmethod
    def parse_package_size(cls, package_size_str: str) -> Tuple[float, str]:
        """Parses commercial retail package sizes (e.g. '1 kg', '500 g', '500 mL', '1 L').

        Returns:
            Tuple of (quantity_in_standard_unit, standard_unit: 'kg' or 'L')
        """
        if not package_size_str or not package_size_str.strip():
            return 1.0, "kg"

        clean_str = package_size_str.strip().lower()
        match = re.search(r"([\d.]+)\s*([a-zA-Z]+)", clean_str)
        if not match:
            return 1.0, "kg"

        val = float(match.group(1))
        unit = match.group(2).lower()

        if unit in ["kg", "kgs", "kilogram", "kilograms"]:
            return val, "kg"
        elif unit in ["g", "gm", "gms", "gram", "grams"]:
            return val / 1000.0, "kg"
        elif unit in ["l", "ltr", "liter", "liters", "litre", "litres"]:
            return val, "L"
        elif unit in ["ml", "milliliter", "milliliters", "millilitre"]:
            return val / 1000.0, "L"
        else:
            return val, "kg"

    @classmethod
    def calculate_required_packages(
        cls,
        substitute_dose_Qs: float,
        field_area_acres: float,
        package_size_str: Optional[str] = None,
        dose_unit: str = "kg/acre",
        product_density_kg_per_l: Optional[float] = None,
    ) -> Tuple[float, int, str]:
        """Computes total chemical quantity required and number of retail packs needed.

        Strictly enforces physical dimension compatibility:
        - Prevents invalid kg-to-litre conversions without density information.
        """
        if field_area_acres <= 0.0:
            raise InvalidDosageError(f"Field area must be strictly positive, got {field_area_acres}")
        if substitute_dose_Qs <= 0.0:
            raise InvalidDosageError(f"Substitute dose Qs must be strictly positive, got {substitute_dose_Qs}")

        total_quantity = round(substitute_dose_Qs * field_area_acres, 4)

        # Determine physical dimension of dosage unit
        d_unit_clean = dose_unit.strip().lower()
        dose_dimension = "MASS" if ("kg" in d_unit_clean or "g" in d_unit_clean) else "VOLUME"

        if not package_size_str:
            pack_capacity = 1.0
            pack_unit = "kg" if dose_dimension == "MASS" else "L"
            pack_desc = f"1.0 {pack_unit}"
        else:
            pack_capacity, pack_unit = cls.parse_package_size(package_size_str)
            pack_desc = f"{pack_capacity} {pack_unit}"

        pack_dimension = "MASS" if pack_unit == "kg" else "VOLUME"

        # Check for invalid cross-dimension without density
        if dose_dimension != pack_dimension:
            if product_density_kg_per_l is None or product_density_kg_per_l <= 0.0:
                raise IncompatibleConcentrationUnitError(
                    f"Physical unit mismatch: dosage is in {dose_dimension} ({dose_unit}) but package "
                    f"size is in {pack_dimension} ({pack_unit}). Conversion between mass and volume requires "
                    "formulation density (kg/L), which is unavailable."
                )
            # Convert pack_capacity to match dosage dimension
            if dose_dimension == "MASS" and pack_dimension == "VOLUME":
                # Package capacity in L converted to kg: Mass = Volume * density
                pack_capacity = pack_capacity * product_density_kg_per_l
            elif dose_dimension == "VOLUME" and pack_dimension == "MASS":
                # Package capacity in kg converted to L: Volume = Mass / density
                pack_capacity = pack_capacity / product_density_kg_per_l

        if pack_capacity <= 0.0:
            pack_capacity = 1.0

        packages_needed = math.ceil(total_quantity / pack_capacity)
        if total_quantity > 0 and packages_needed < 1:
            packages_needed = 1

        return total_quantity, packages_needed, pack_desc

    @classmethod
    def validate_formulation_for_application(
        cls,
        formulation_type: str,
        application_method: str = "Foliar Spray",
    ) -> bool:
        """Validates whether a product's formulation matches the prescribed application method."""
        form_clean = formulation_type.strip().upper()
        app_clean = application_method.strip().lower()

        if "foliar" in app_clean or "spray" in app_clean:
            if form_clean in NON_FOLIAR_FORMULATION_TYPES:
                return False
            return True

        if "soil" in app_clean or "drench" in app_clean:
            return True

        return True

    @classmethod
    def validate_crop_and_disease_registration(
        cls,
        registered_crops: Optional[str],
        registered_diseases: Optional[str],
        target_crop: str,
        target_disease: str,
    ) -> bool:
        """Confirms that the product is officially registered for the specific crop and disease."""
        if not registered_crops or not registered_diseases:
            return False

        crops_list = [c.strip().lower() for c in registered_crops.split(",") if c.strip()]
        diseases_list = [d.strip().lower() for d in registered_diseases.split(",") if d.strip()]

        target_crop_clean = target_crop.strip().lower()
        target_disease_clean = target_disease.strip().lower()

        crop_matched = any(target_crop_clean in c for c in crops_list)
        disease_matched = any(target_disease_clean in d for d in diseases_list)

        return crop_matched and disease_matched

    @classmethod
    def evaluate_product_eligibility(
        cls,
        product_brand: str,
        product_active_ingredient: str,
        product_formulation: str,
        is_legally_registered: bool,
        registration_number: Optional[str],
        registered_crops: Optional[str],
        registered_diseases: Optional[str],
        required_active_ingredient: str,
        target_crop: str,
        target_disease: str,
        prescribed_application_method: str = "Foliar Spray",
    ) -> Tuple[bool, str]:
        """Evaluates whether a commercial agrochemical is an authorized legal substitute.

        Returns:
            Tuple of (is_eligible: bool, reason_or_error_message: str)
        """
        # Rule 1: Active Ingredient Match
        if product_active_ingredient.strip().lower() != required_active_ingredient.strip().lower():
            return False, f"Active ingredient mismatch: '{product_active_ingredient}' != '{required_active_ingredient}'"

        # Rule 2: Legal Registration Check
        if not is_legally_registered or not registration_number or registration_number.strip().upper() in ["EXPIRED", "UNREGISTERED", "NONE", ""]:
            return False, f"Product lacks valid statutory CIBRC registration (Registration: '{registration_number}')"

        # Rule 3: Formulation Compatibility
        if not cls.validate_formulation_for_application(product_formulation, prescribed_application_method):
            non_foliar_desc = NON_FOLIAR_FORMULATION_TYPES.get(product_formulation.upper(), product_formulation)
            return False, f"Incompatible formulation '{product_formulation}' ({non_foliar_desc}) for application method '{prescribed_application_method}'"

        # Rule 4: Crop & Disease Specific Registration
        if not cls.validate_crop_and_disease_registration(registered_crops, registered_diseases, target_crop, target_disease):
            return False, f"Not officially registered for crop '{target_crop}' and disease '{target_disease}' (Registered: crops='{registered_crops}', diseases='{registered_diseases}')"

        return True, "Eligible registered substitute"
