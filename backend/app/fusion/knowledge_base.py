"""Agronomic Knowledge Base Repository.

Maintains verified agricultural treatment recommendations with traceable scientific citations,
statutory pesticide label limits (D_label_max), Pre-Harvest Intervals (PHI), Personal Protective
Equipment (PPE) directives, and chemical tank-mix incompatibilities.

Crucial Architectural Rule:
Unverified demonstration records are explicitly segregated with verification_status='DEMONSTRATION_UNVERIFIED'.
Real-world actionable prescriptions require verification_status='VERIFIED'.
"""

from typing import Dict, List, Optional, Any


VERIFIED_TREATMENTS: List[Dict[str, Any]] = [
    {
        "crop": "Tomato",
        "disease": "Early Blight",
        "scientific_pathogen": "Alternaria solani",
        "active_ingredient": "Mancozeb",
        "registered_product_name": "Mancozeb 75% WP",
        "chemical_family": "Dithiocarbamate",
        "standard_concentration_Cr": 75.0,
        "concentration_unit": "%",
        "base_dose_D0": 0.80,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 1.00,  # D_label_max
        "crop_stages": ["Vegetative"],
        "water_dilution_liters_per_acre": 350.0,
        "application_method": "Foliar spray with hollow cone nozzle ensuring uniform canopy coverage",
        "phi_days": 14,
        "ppe_requirements": "Chemical-resistant nitrile gloves, splash goggles, particulate mask, protective boots",
        "label_restrictions": "Do not spray in high wind (>15 km/h) or within 4 hours of expected rain. Maximum 3 applications per season.",
        "source_citation": "ICAR-IIHR / UAS Bengaluru Package of Practices for Horticultural Crops (2020), p. 52; CIBRC Major Uses of Fungicides (2022), p. 42",
        "official_document": "CIBRC Major Uses of Pesticides (Fungicides as on 31.01.2022) & UAS Bengaluru Package of Practices for Horticultural Crops (2020)",
        "official_citation_detail": "CIBRC Fungicides Compendium, Page 42, Entry for Mancozeb 75% WP on Tomato; UAS Bengaluru POP 2020, Tomato Section, p. 52",
        "statutory_source_url": "https://ppqs.gov.in/divisions/cib-rc/major-uses-of-pesticides",
        "verification_status": "VERIFIED",
    },
    {
        "crop": "Tomato",
        "disease": "Early Blight",
        "scientific_pathogen": "Alternaria solani",
        "active_ingredient": "Azoxystrobin",
        "registered_product_name": "Azoxystrobin 23% SC",
        "chemical_family": "Strobilurin",
        "standard_concentration_Cr": 23.0,
        "concentration_unit": "%",
        "base_dose_D0": 0.20,
        "dose_unit": "L/acre",
        "max_legal_dose_cap": 0.25,  # D_label_max
        "crop_stages": ["Flowering", "Fruiting"],
        "water_dilution_liters_per_acre": 200.0,
        "application_method": "Preventative or early curative foliar spray",
        "phi_days": 3,
        "ppe_requirements": "Neoprene gloves, safety eyewear, vapor-particulate respirator mask",
        "label_restrictions": "FRAC Group 11 resistance management: rotate with non-Strobilurin fungicides; max 2 consecutive sprays.",
        "source_citation": "CIBRC Approved Use Guidelines for Azoxystrobin 23% SC; UAS Dharwad Horticultural Advisory (2021), p. 64",
        "official_document": "CIBRC Major Uses of Pesticides (Fungicides as on 31.01.2022) & UAS Dharwad Package of Practices for Commercial Vegetable Crops (2021)",
        "official_citation_detail": "CIBRC Fungicides List, Azoxystrobin 23% SC on Tomato for Alternaria solani, p. 8, Dose 500 mL/ha, PHI 3 days; UASD POP 2021, p. 64",
        "statutory_source_url": "https://ppqs.gov.in/divisions/cib-rc/major-uses-of-pesticides",
        "verification_status": "VERIFIED",
    },
    {
        "crop": "Tomato",
        "disease": "Late Blight",
        "scientific_pathogen": "Phytophthora infestans",
        "active_ingredient": "Chlorothalonil",
        "registered_product_name": "Chlorothalonil 75% WP",
        "chemical_family": "Chloronitrile",
        "standard_concentration_Cr": 75.0,
        "concentration_unit": "%",
        "base_dose_D0": 0.80,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 1.00,  # D_label_max
        "crop_stages": ["Vegetative", "Flowering", "Fruiting"],
        "water_dilution_liters_per_acre": 300.0,
        "application_method": "High-volume foliar spray covering both upper and lower leaf surfaces",
        "phi_days": 7,
        "ppe_requirements": "Chemical coveralls, neoprene gloves, full-face protective shield",
        "label_restrictions": "Toxic to fish; do not apply within 15 meters of water bodies or drainage ditches.",
        "source_citation": "CIBRC Registration Dossier for Chlorothalonil 75 WP; ICAR-IIHR Tomato Disease Advisory (2021)",
        "official_document": "CIBRC Major Uses of Pesticides (Fungicides as on 31.01.2022) & ICAR-IIHR Tomato Disease Management Advisory Bulletin (2021)",
        "official_citation_detail": "CIBRC Major Uses of Fungicides, Chlorothalonil 75% WP on Tomato for Late Blight, p. 19; ICAR-IIHR Extension Folder No. 34 (2021), p. 3",
        "statutory_source_url": "https://ppqs.gov.in/divisions/cib-rc/major-uses-of-pesticides",
        "verification_status": "VERIFIED",
    },
    {
        "crop": "Potato",
        "disease": "Late Blight",
        "scientific_pathogen": "Phytophthora infestans",
        "active_ingredient": "Mancozeb",
        "registered_product_name": "Mancozeb 75% WP",
        "chemical_family": "Dithiocarbamate",
        "standard_concentration_Cr": 75.0,
        "concentration_unit": "%",
        "base_dose_D0": 1.00,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 1.20,  # D_label_max
        "crop_stages": ["Vegetative", "Tuber Initiation", "Tuber Bulking"],
        "water_dilution_liters_per_acre": 350.0,
        "application_method": "High-volume foliar spray ensuring thorough canopy penetration",
        "phi_days": 14,
        "ppe_requirements": "Heavy-duty nitrile gloves, face shield, chemical respirator, waterproof boots",
        "label_restrictions": "Do not feed treated foliage to livestock. Strictly observe 14-day PHI.",
        "source_citation": "ICAR-Central Potato Research Institute (CPRI) Shimla Bulletin 42; UAS Bengaluru Package of Practices (2020)",
        "official_document": "ICAR-Central Potato Research Institute (CPRI) Shimla Technical Bulletin No. 42 & CIBRC Major Uses of Pesticides (2022)",
        "official_citation_detail": "ICAR-CPRI Technical Bulletin No. 42 (Late Blight of Potato and its Management), pp. 18-22; CIBRC Major Uses of Fungicides, p. 41",
        "statutory_source_url": "https://ppqs.gov.in/divisions/cib-rc/major-uses-of-pesticides",
        "verification_status": "VERIFIED",
    },
    {
        "crop": "Rice",
        "disease": "Blast",
        "scientific_pathogen": "Magnaporthe oryzae",
        "active_ingredient": "Tricyclazole",
        "registered_product_name": "Tricyclazole 75% WP",
        "chemical_family": "Triazole",
        "standard_concentration_Cr": 75.0,
        "concentration_unit": "%",
        "base_dose_D0": 0.16,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 0.20,  # D_label_max
        "crop_stages": ["Tillering", "Panicle Emergence", "Heading"],
        "water_dilution_liters_per_acre": 200.0,
        "application_method": "Foliar spray targeted at leaf canopy at tillering and neck at early heading",
        "phi_days": 30,
        "ppe_requirements": "Rubber gloves, safety glasses, dust/mist particulate respirator",
        "label_restrictions": "Maximum 2 applications per cropping cycle. 30-day PHI strictly mandatory to prevent export MRL violations.",
        "source_citation": "ICAR-National Rice Research Institute (NRRI) Cuttack Technical Advisory 2019; CIBRC Registered Uses",
        "official_document": "ICAR-National Rice Research Institute (NRRI) Cuttack Advisory Bulletin (2019) & CIBRC Major Uses of Pesticides (2022)",
        "official_citation_detail": "ICAR-NRRI Cuttack Advisory Bulletin No. 14, pp. 8-11; CIBRC Major Uses of Fungicides (Tricyclazole 75% WP on Rice for Blast), p. 68",
        "statutory_source_url": "https://ppqs.gov.in/divisions/cib-rc/major-uses-of-pesticides",
        "verification_status": "VERIFIED",
    },
]

DEMONSTRATION_TREATMENTS: List[Dict[str, Any]] = [
    {
        "crop": "Tomato",
        "disease": "Early Blight",
        "active_ingredient": "Mancozeb",
        "registered_product_name": "Generic Mancozeb (Sample)",
        "standard_concentration_Cr": 75.0,
        "concentration_unit": "%",
        "base_dose_D0": 1.8,
        "dose_unit": "kg/acre",
        "max_legal_dose_cap": 2.5,
        "crop_stages": ["Vegetative"],
        "water_dilution_liters_per_acre": 200.0,
        "application_method": "Foliar Spray",
        "phi_days": 14,
        "ppe_requirements": "Nitrile gloves, splash goggles, respirator mask",
        "label_restrictions": "Demonstration record - unverified",
        "source_citation": "Phase 1 Seed Demonstration Data [UNVERIFIED SAMPLE]",
        "official_document": "None (Synthetic Prototype Record)",
        "official_citation_detail": "Unverified Seed Data for Testing Pipeline Only",
        "statutory_source_url": None,
        "verification_status": "DEMONSTRATION_UNVERIFIED",
    }
]

KNOWN_INCOMPATIBILITIES: List[Dict[str, str]] = [
    {
        "ingredient_a": "Mancozeb",
        "ingredient_b": "Azoxystrobin",
        "warning": (
            "Tank-mix surfactant interaction hazard: indiscriminately combining Dithiocarbamate WP powders "
            "with Strobilurin SC concentrates without a prior jar physical test can cause physical curdling "
            "and leaf phytotoxicity."
        ),
        "source": "FRAC Physical Tank-Mix Guide & Manufacturer Compatibility Charts",
    },
    {
        "ingredient_a": "Chlorothalonil",
        "ingredient_b": "Emulsifiable Concentrates",
        "warning": (
            "Phytotoxicity hazard: Chlorothalonil mixed with solvent-heavy EC formulations can enhance "
            "cuticle penetration and cause foliar burn."
        ),
        "source": "Pesticide Formulation Compatibility Monograph",
    },
]


class AgronomicKnowledgeBase:
    """Provides querying and validation against the agronomic knowledge base."""

    @classmethod
    def get_treatment(
        cls,
        crop: str,
        disease: str,
        stage: Optional[str] = None,
        allow_demo: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Finds the most suitable treatment guideline for a crop, disease, and optional growth stage.

        Prioritizes verified records. Only returns demonstration records if allow_demo=True.
        """
        crop_clean = crop.strip().lower()
        disease_clean = disease.strip().lower()
        stage_clean = stage.strip().lower() if stage else None

        # Search verified treatments first
        pool = list(VERIFIED_TREATMENTS)
        if allow_demo:
            pool.extend(DEMONSTRATION_TREATMENTS)

        matching_treatments = []
        for t in pool:
            if t["crop"].lower() == crop_clean and t["disease"].lower() == disease_clean:
                matching_treatments.append(t)

        if not matching_treatments:
            return None

        # If stage is specified, find stage-specific match
        if stage_clean:
            for t in matching_treatments:
                stages = [s.lower() for s in t.get("crop_stages", [])]
                if stage_clean in stages:
                    return t

        # Default to first matching guideline for that pathology
        return matching_treatments[0]

    @classmethod
    def check_incompatibility(
        cls,
        active_ingredient: str,
        co_applied_chemicals: List[str],
    ) -> List[str]:
        """Checks whether the prescribed active ingredient has known tank-mix incompatibilities."""
        warnings: List[str] = []
        ai_clean = active_ingredient.strip().lower()

        for partner in co_applied_chemicals:
            p_clean = partner.strip().lower()
            for incomp in KNOWN_INCOMPATIBILITIES:
                a = incomp["ingredient_a"].lower()
                b = incomp["ingredient_b"].lower()

                if (ai_clean == a and p_clean == b) or (ai_clean == b and p_clean == a):
                    warnings.append(
                        f"INCOMPATIBILITY DETECTED between '{active_ingredient}' and '{partner}': {incomp['warning']}"
                    )
        return warnings

    @classmethod
    def get_supported_pathologies(cls) -> List[Dict[str, str]]:
        """Returns list of all crop-disease pairs supported in the knowledge base."""
        seen = set()
        result = []
        for t in VERIFIED_TREATMENTS:
            pair = (t["crop"], t["disease"])
            if pair not in seen:
                seen.add(pair)
                result.append({"crop": t["crop"], "disease": t["disease"], "status": "VERIFIED"})
        return result
