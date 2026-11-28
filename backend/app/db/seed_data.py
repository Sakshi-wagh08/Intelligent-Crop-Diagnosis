"""Agronomic Knowledge Base and Seed Data Repository.

IMPORTANT NOTICE:
All records below are synthetic demonstration (DEMO) entries established strictly for
research architecture validation, algorithmic development, and software testing.
These dosage values and chemical associations are NOT officially certified agricultural
prescriptions and must NEVER be utilized for actual agricultural field applications.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from backend.app.models.crop import Crop
from backend.app.models.disease import Disease
from backend.app.models.chemical import ActiveIngredient, BaseTreatment
from backend.app.models.merchant import Merchant, Product
from backend.app.models.incompatibility import ChemicalIncompatibility
from backend.app.core.logging import logger

DEMO_DISCLAIMER = (
    "[DEMO / UNVERIFIED SAMPLE DATA FOR RESEARCH PROTOCOL ONLY - NOT FOR FIELD USE]"
)

# Seed Crops
SEED_CROPS = [
    {
        "name": "Tomato",
        "scientific_name": "Solanum lycopersicum",
        "description": f"Common nightshade crop cultivated worldwide. {DEMO_DISCLAIMER}",
    },
    {
        "name": "Potato",
        "scientific_name": "Solanum tuberosum",
        "description": f"Major root tuber staple crop. {DEMO_DISCLAIMER}",
    },
    {
        "name": "Rice",
        "scientific_name": "Oryza sativa",
        "description": f"Primary cereal crop across Asia and tropical regions. {DEMO_DISCLAIMER}",
    },
]

# Seed Diseases
SEED_DISEASES = [
    # Tomato Diseases
    {
        "crop_name": "Tomato",
        "disease_name": "Early Blight",
        "scientific_name": "Alternaria solani",
        "pathogen_type": "Fungal",
        "symptoms": "Dark brown concentric target-like rings on mature leaves, leading to defoliation.",
    },
    {
        "crop_name": "Tomato",
        "disease_name": "Late Blight",
        "scientific_name": "Phytophthora infestans",
        "pathogen_type": "Fungal (Oomycete)",
        "symptoms": "Water-soaked lesions on leaves turning dark brown/purplish with white fungal bloom in humid conditions.",
    },
    # Potato Diseases
    {
        "crop_name": "Potato",
        "disease_name": "Late Blight",
        "scientific_name": "Phytophthora infestans",
        "pathogen_type": "Fungal (Oomycete)",
        "symptoms": "Rapid blighting of leaves, stems and water-soaked lesions on tubers.",
    },
    # Rice Diseases
    {
        "crop_name": "Rice",
        "disease_name": "Blast",
        "scientific_name": "Magnaporthe oryzae",
        "pathogen_type": "Fungal",
        "symptoms": "Spindle-shaped elliptical lesions with gray centers and brown borders on leaves and neck.",
    },
]

# Seed Active Ingredients
SEED_ACTIVE_INGREDIENTS = [
    {
        "common_name": "Mancozeb",
        "chemical_family": "Dithiocarbamate",
        "standard_concentration_Cr": 75.0,  # Reference Cr = 75.0%
        "concentration_unit": "%",
        "max_legal_dose_cap": 2.5,  # Max 2.5 kg/acre
        "phi_days": 14,
        "ppe_requirements": "Nitrile/rubber gloves, splash goggles, particulate respirator mask, protective boots.",
        "is_demo": True,
    },
    {
        "common_name": "Chlorothalonil",
        "chemical_family": "Chloronitrile",
        "standard_concentration_Cr": 75.0,  # Reference Cr = 75.0%
        "concentration_unit": "%",
        "max_legal_dose_cap": 2.0,  # Max 2.0 kg/acre
        "phi_days": 7,
        "ppe_requirements": "Full chemical coveralls, neoprene gloves, full-face shield.",
        "is_demo": True,
    },
    {
        "common_name": "Azoxystrobin",
        "chemical_family": "Strobilurin",
        "standard_concentration_Cr": 23.0,  # Reference Cr = 23.0% SC
        "concentration_unit": "%",
        "max_legal_dose_cap": 0.5,  # Max 0.5 L/acre
        "phi_days": 5,
        "ppe_requirements": "Chemical resistant gloves, eye goggles, long-sleeved shirt.",
        "is_demo": True,
    },
    {
        "common_name": "Tricyclazole",
        "chemical_family": "Triazole",
        "standard_concentration_Cr": 75.0,  # Reference Cr = 75.0% WP
        "concentration_unit": "%",
        "max_legal_dose_cap": 0.4,  # Max 0.4 kg/acre
        "phi_days": 30,
        "ppe_requirements": "Dust/mist respirator, rubber gloves, protective glasses.",
        "is_demo": True,
    },
    {
        "common_name": "Urea",
        "chemical_family": "Nitrogenous Fertilizer (Carbamide)",
        "standard_concentration_Cr": 46.0,  # Reference Cr = 46.0% N
        "concentration_unit": "%",
        "max_legal_dose_cap": 60.0,  # Max 60 kg/acre split dose cap
        "phi_days": 0,
        "ppe_requirements": "Wash hands after soil broadcasting; store in dry place.",
        "is_demo": True,
    },
]

# Seed Base Treatments (Package-of-Practices Demonstration Records)
SEED_BASE_TREATMENTS = [
    {
        "crop_name": "Tomato",
        "disease_name": "Early Blight",
        "active_ingredient": "Mancozeb",
        "crop_stage": "Vegetative",
        "base_dose_D0": 1.8,
        "dose_unit": "kg/acre",
        "water_dilution_liters_per_acre": 200.0,
        "application_method": "Foliar Spray",
        "application_timing": "Apply at first sign of circular lesions during early morning before high heat.",
        "is_demo": True,
    },
    {
        "crop_name": "Tomato",
        "disease_name": "Early Blight",
        "active_ingredient": "Azoxystrobin",
        "crop_stage": "Flowering",
        "base_dose_D0": 0.4,
        "dose_unit": "L/acre",
        "water_dilution_liters_per_acre": 200.0,
        "application_method": "Foliar Spray",
        "application_timing": "Preventative spray during humid conditions before lesion sporulation.",
        "is_demo": True,
    },
    {
        "crop_name": "Tomato",
        "disease_name": "Late Blight",
        "active_ingredient": "Chlorothalonil",
        "crop_stage": "Vegetative",
        "base_dose_D0": 1.5,
        "dose_unit": "kg/acre",
        "water_dilution_liters_per_acre": 250.0,
        "application_method": "Foliar Spray",
        "application_timing": "Apply upon first disease forecast warning or cool humid weather.",
        "is_demo": True,
    },
    {
        "crop_name": "Potato",
        "disease_name": "Late Blight",
        "active_ingredient": "Mancozeb",
        "crop_stage": "Tuber Initiation",
        "base_dose_D0": 2.0,
        "dose_unit": "kg/acre",
        "water_dilution_liters_per_acre": 200.0,
        "application_method": "Foliar Spray",
        "application_timing": "Thorough coverage of both upper and lower canopy foliage.",
        "is_demo": True,
    },
    {
        "crop_name": "Rice",
        "disease_name": "Blast",
        "active_ingredient": "Tricyclazole",
        "crop_stage": "Tillering",
        "base_dose_D0": 0.35,
        "dose_unit": "kg/acre",
        "water_dilution_liters_per_acre": 200.0,
        "application_method": "Foliar Spray",
        "application_timing": "Apply at tillering stage upon detection of spindle lesions.",
        "is_demo": True,
    },
]

# Seed Fictional Merchants (Geolocated demonstration agro-dealers in Karnataka agricultural belt)
SEED_MERCHANTS = [
    {
        "name": "Kisan Seva Kendra [DEMO Agro-Dealer]",
        "contact_phone": "+91-9876543201",
        "contact_email": "demo.kisan.seva@agri-example.test",
        "address": "Shop No. 12, APMC Market Yard, Mandya, Karnataka, India",
        "lat": 12.5230,
        "lon": 76.8980,
        "is_active": True,
        "is_demo": True,
    },
    {
        "name": "Sri Lakshmi Agri Inputs [DEMO Agro-Dealer]",
        "contact_phone": "+91-9876543202",
        "contact_email": "demo.lakshmi.agri@agri-example.test",
        "address": "B.M. Road, Ramanagara, Karnataka, India",
        "lat": 12.7210,
        "lon": 77.2810,
        "is_active": True,
        "is_demo": True,
    },
    {
        "name": "Green Valley Farm Supplies [DEMO Agro-Dealer]",
        "contact_phone": "+91-9876543203",
        "contact_email": "demo.greenvalley@agri-example.test",
        "address": "Mysore Main Road, Kengeri, Bengaluru, Karnataka, India",
        "lat": 12.9120,
        "lon": 77.4850,
        "is_active": True,
        "is_demo": True,
    },
]

# Seed Products (Demonstrating concentration variations Cs vs reference Cr)
SEED_PRODUCTS = [
    # Indofil M-45 (Exact concentration Cs = 75.0%) at Kisan Seva Kendra
    {
        "merchant_name": "Kisan Seva Kendra [DEMO Agro-Dealer]",
        "active_ingredient": "Mancozeb",
        "brand_name": "DemoIndo Mancozeb 75 WP [DEMO]",
        "concentration_Cs": 75.0,
        "concentration_unit": "%",
        "formulation_type": "WP",
        "package_size": "1 kg",
        "price": 420.0,
        "stock_quantity": 25,
        "registration_number": "CIB-DEMO-2026-001",
        "registered_crops": "Tomato, Potato",
        "registered_diseases": "Early Blight, Late Blight",
        "application_method": "Foliar Spray",
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Higher concentration formulation (Cs = 80.0%) demonstrating concentration adjustment Qs = Qr * (75/80)
    {
        "merchant_name": "Sri Lakshmi Agri Inputs [DEMO Agro-Dealer]",
        "active_ingredient": "Mancozeb",
        "brand_name": "DemoCrop Mancozeb 80 WP [DEMO]",
        "concentration_Cs": 80.0,
        "concentration_unit": "%",
        "formulation_type": "WP",
        "package_size": "1 kg",
        "price": 460.0,
        "stock_quantity": 14,
        "registration_number": "CIB-DEMO-2026-002",
        "registered_crops": "Tomato, Potato",
        "registered_diseases": "Early Blight, Late Blight",
        "application_method": "Foliar Spray",
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Chlorothalonil at Sri Lakshmi Agri Inputs
    {
        "merchant_name": "Sri Lakshmi Agri Inputs [DEMO Agro-Dealer]",
        "active_ingredient": "Chlorothalonil",
        "brand_name": "DemoShield Chloro 75 WP [DEMO]",
        "concentration_Cs": 75.0,
        "concentration_unit": "%",
        "formulation_type": "WP",
        "package_size": "500 g",
        "price": 380.0,
        "stock_quantity": 8,
        "registration_number": "CIB-DEMO-2026-003",
        "registered_crops": "Tomato",
        "registered_diseases": "Late Blight",
        "application_method": "Foliar Spray",
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Azoxystrobin 23% SC at Green Valley Farm Supplies
    {
        "merchant_name": "Green Valley Farm Supplies [DEMO Agro-Dealer]",
        "active_ingredient": "Azoxystrobin",
        "brand_name": "DemoStrobin 23 SC [DEMO]",
        "concentration_Cs": 23.0,
        "concentration_unit": "%",
        "formulation_type": "SC",
        "package_size": "500 mL",
        "price": 750.0,
        "stock_quantity": 12,
        "registration_number": "CIB-DEMO-2026-004",
        "registered_crops": "Tomato",
        "registered_diseases": "Early Blight",
        "application_method": "Foliar Spray",
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Tricyclazole 75% WP at Kisan Seva Kendra
    {
        "merchant_name": "Kisan Seva Kendra [DEMO Agro-Dealer]",
        "active_ingredient": "Tricyclazole",
        "brand_name": "DemoBlast Tricyclo 75 WP [DEMO]",
        "concentration_Cs": 75.0,
        "concentration_unit": "%",
        "formulation_type": "WP",
        "package_size": "250 g",
        "price": 310.0,
        "stock_quantity": 30,
        "registration_number": "CIB-DEMO-2026-005",
        "registered_crops": "Rice",
        "registered_diseases": "Blast",
        "application_method": "Foliar Spray",
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Out-of-stock product at Green Valley (tests stock availability filtering / ranking exclusion)
    {
        "merchant_name": "Green Valley Farm Supplies [DEMO Agro-Dealer]",
        "active_ingredient": "Mancozeb",
        "brand_name": "DemoStockout Mancozeb 75 WP [DEMO]",
        "concentration_Cs": 75.0,
        "concentration_unit": "%",
        "formulation_type": "WP",
        "package_size": "1 kg",
        "price": 410.0,
        "stock_quantity": 0,  # OUT OF STOCK
        "registration_number": "CIB-DEMO-2026-006",
        "registered_crops": "Tomato, Potato",
        "registered_diseases": "Early Blight, Late Blight",
        "application_method": "Foliar Spray",
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Product registered for a different crop (Cotton) to test crop mismatch rejection
    {
        "merchant_name": "Sri Lakshmi Agri Inputs [DEMO Agro-Dealer]",
        "active_ingredient": "Mancozeb",
        "brand_name": "DemoCotton Mancozeb 75 WP [DEMO]",
        "concentration_Cs": 75.0,
        "concentration_unit": "%",
        "formulation_type": "WP",
        "package_size": "1 kg",
        "price": 430.0,
        "stock_quantity": 15,
        "registration_number": "CIB-DEMO-2026-007",
        "registered_crops": "Cotton",  # Cotton only
        "registered_diseases": "Leaf Spot",
        "application_method": "Foliar Spray",
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Unregistered product testing item kept legally registered in seed to preserve Phase 1 invariants
    {
        "merchant_name": "Kisan Seva Kendra [DEMO Agro-Dealer]",
        "active_ingredient": "Mancozeb",
        "brand_name": "DemoGeneric Mancozeb 75 WP [DEMO]",
        "concentration_Cs": 75.0,
        "concentration_unit": "%",
        "formulation_type": "WP",
        "package_size": "1 kg",
        "price": 350.0,
        "stock_quantity": 20,
        "registration_number": "CIB-DEMO-2026-009",
        "registered_crops": "Tomato",
        "registered_diseases": "Early Blight",
        "application_method": "Foliar Spray",
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Incompatible non-foliar formulation (Granules) to test application method rejection
    {
        "merchant_name": "Sri Lakshmi Agri Inputs [DEMO Agro-Dealer]",
        "active_ingredient": "Mancozeb",
        "brand_name": "DemoGranule Mancozeb 5 GR [DEMO]",
        "concentration_Cs": 5.0,
        "concentration_unit": "%",
        "formulation_type": "GR",  # Granules
        "package_size": "5 kg",
        "price": 500.0,
        "stock_quantity": 10,
        "registration_number": "CIB-DEMO-2026-008",
        "registered_crops": "Tomato",
        "registered_diseases": "Early Blight",
        "application_method": "Soil Application / Broadcast",  # NOT FOLIAR
        "is_legally_registered": True,
        "is_demo": True,
    },
    # Soil-Applied Fertilizer Offerings (Urea 46% N)
    {
        "merchant_name": "Kisan Seva Kendra [DEMO Agro-Dealer]",
        "active_ingredient": "Urea",
        "brand_name": "DemoNeem Coated Urea 46% N [DEMO]",
        "concentration_Cs": 46.0,
        "concentration_unit": "%",
        "formulation_type": "GR",
        "package_size": "45 kg",
        "price": 266.0,
        "stock_quantity": 40,
        "registration_number": "FCO-DEMO-2026-101",
        "registered_crops": "Tomato, Potato, Rice",
        "registered_diseases": "Healthy, Early Blight, Late Blight, Blast, Soil Nutrition",
        "application_method": "Soil Application",
        "is_legally_registered": True,
        "is_demo": True,
    },
    {
        "merchant_name": "Green Valley Farm Supplies [DEMO Agro-Dealer]",
        "active_ingredient": "Urea",
        "brand_name": "DemoAgri Urea 46% N [DEMO]",
        "concentration_Cs": 46.0,
        "concentration_unit": "%",
        "formulation_type": "GR",
        "package_size": "25 kg",
        "price": 175.0,
        "stock_quantity": 20,
        "registration_number": "FCO-DEMO-2026-102",
        "registered_crops": "Tomato, Potato, Rice",
        "registered_diseases": "Healthy, Early Blight, Late Blight, Blast, Soil Nutrition",
        "application_method": "Soil Application",
        "is_legally_registered": True,
        "is_demo": True,
    },
]

# Chemical Incompatibilities (Tank-Mix Phytotoxicity Conflicts)
SEED_INCOMPATIBILITIES = [
    {
        "ingredient_a": "Mancozeb",
        "ingredient_b": "Azoxystrobin",
        "warning_message": (
            "[DEMO WARNING] Avoid indiscriminate tank mixing of Dithiocarbamates with Strobilurin "
            "concentrates without jar testing. Incompatible surfactants can induce leaf phytotoxicity."
        ),
        "incompatibility_type": "Tank-mix surfactant interaction hazard",
        "is_demo": True,
    }
]


def seed_database(db: Session) -> Dict[str, int]:
    """Populates the database with initial demonstration agronomic knowledge base and merchant data."""
    counts = {
        "crops": 0,
        "diseases": 0,
        "active_ingredients": 0,
        "base_treatments": 0,
        "merchants": 0,
        "products": 0,
        "incompatibilities": 0,
    }

    # 1. Seed Crops
    crop_map: Dict[str, Crop] = {}
    for item in SEED_CROPS:
        existing = db.query(Crop).filter(Crop.name == item["name"]).first()
        if not existing:
            crop = Crop(**item)
            db.add(crop)
            db.flush()
            crop_map[crop.name] = crop
            counts["crops"] += 1
        else:
            crop_map[existing.name] = existing

    # 2. Seed Diseases
    disease_map: Dict[str, Disease] = {}
    for item in SEED_DISEASES:
        crop = crop_map.get(item["crop_name"])
        if not crop:
            continue
        existing = (
            db.query(Disease)
            .filter(
                Disease.crop_id == crop.id,
                Disease.disease_name == item["disease_name"],
            )
            .first()
        )
        key = f"{crop.name}:{item['disease_name']}"
        if not existing:
            disease = Disease(
                crop_id=crop.id,
                disease_name=item["disease_name"],
                scientific_name=item["scientific_name"],
                pathogen_type=item["pathogen_type"],
                symptoms=item["symptoms"],
            )
            db.add(disease)
            db.flush()
            disease_map[key] = disease
            counts["diseases"] += 1
        else:
            disease_map[key] = existing

    # 3. Seed Active Ingredients
    ingredient_map: Dict[str, ActiveIngredient] = {}
    for item in SEED_ACTIVE_INGREDIENTS:
        existing = (
            db.query(ActiveIngredient)
            .filter(ActiveIngredient.common_name == item["common_name"])
            .first()
        )
        if not existing:
            ingredient = ActiveIngredient(**item)
            db.add(ingredient)
            db.flush()
            ingredient_map[ingredient.common_name] = ingredient
            counts["active_ingredients"] += 1
        else:
            ingredient_map[existing.common_name] = existing

    # 4. Seed Base Treatments
    for item in SEED_BASE_TREATMENTS:
        d_key = f"{item['crop_name']}:{item['disease_name']}"
        disease = disease_map.get(d_key)
        ingredient = ingredient_map.get(item["active_ingredient"])
        if not disease or not ingredient:
            continue

        existing = (
            db.query(BaseTreatment)
            .filter(
                BaseTreatment.disease_id == disease.id,
                BaseTreatment.active_ingredient_id == ingredient.id,
                BaseTreatment.crop_stage == item["crop_stage"],
            )
            .first()
        )
        if not existing:
            treatment = BaseTreatment(
                disease_id=disease.id,
                active_ingredient_id=ingredient.id,
                crop_stage=item["crop_stage"],
                base_dose_D0=item["base_dose_D0"],
                dose_unit=item["dose_unit"],
                water_dilution_liters_per_acre=item["water_dilution_liters_per_acre"],
                application_method=item["application_method"],
                application_timing=item["application_timing"],
                is_demo=item["is_demo"],
            )
            db.add(treatment)
            counts["base_treatments"] += 1

    # 5. Seed Merchants
    merchant_map: Dict[str, Merchant] = {}
    for item in SEED_MERCHANTS:
        existing = db.query(Merchant).filter(Merchant.name == item["name"]).first()
        # Create WKT point: POINT(longitude latitude)
        wkt_geom = f"POINT({item['lon']} {item['lat']})"
        if not existing:
            merchant = Merchant(
                name=item["name"],
                contact_phone=item["contact_phone"],
                contact_email=item["contact_email"],
                address=item["address"],
                location_geom=wkt_geom,
                is_active=item["is_active"],
                is_demo=item["is_demo"],
            )
            db.add(merchant)
            db.flush()
            merchant_map[merchant.name] = merchant
            counts["merchants"] += 1
        else:
            merchant_map[existing.name] = existing

    # 6. Seed Products
    for item in SEED_PRODUCTS:
        merchant = merchant_map.get(item["merchant_name"])
        ingredient = ingredient_map.get(item["active_ingredient"])
        if not merchant or not ingredient:
            continue

        existing = (
            db.query(Product)
            .filter(
                Product.merchant_id == merchant.id,
                Product.brand_name == item["brand_name"],
            )
            .first()
        )
        if not existing:
            product = Product(
                merchant_id=merchant.id,
                active_ingredient_id=ingredient.id,
                brand_name=item["brand_name"],
                concentration_Cs=item["concentration_Cs"],
                concentration_unit=item.get("concentration_unit", "%"),
                formulation_type=item["formulation_type"],
                package_size=item["package_size"],
                price=item["price"],
                stock_quantity=item["stock_quantity"],
                registration_number=item["registration_number"],
                registered_crops=item.get("registered_crops"),
                registered_diseases=item.get("registered_diseases"),
                application_method=item.get("application_method", "Foliar Spray"),
                is_legally_registered=item["is_legally_registered"],
                is_demo=item["is_demo"],
            )
            db.add(product)
            counts["products"] += 1

    # 7. Seed Incompatibilities
    for item in SEED_INCOMPATIBILITIES:
        ing_a = ingredient_map.get(item["ingredient_a"])
        ing_b = ingredient_map.get(item["ingredient_b"])
        if not ing_a or not ing_b:
            continue

        existing = (
            db.query(ChemicalIncompatibility)
            .filter(
                ChemicalIncompatibility.ingredient_a_id == ing_a.id,
                ChemicalIncompatibility.ingredient_b_id == ing_b.id,
            )
            .first()
        )
        if not existing:
            inc = ChemicalIncompatibility(
                ingredient_a_id=ing_a.id,
                ingredient_b_id=ing_b.id,
                warning_message=item["warning_message"],
                incompatibility_type=item["incompatibility_type"],
                is_demo=item["is_demo"],
            )
            db.add(inc)
            counts["incompatibilities"] += 1

    db.commit()
    logger.info(f"Database seeded successfully with demo records: {counts}")
    return counts
