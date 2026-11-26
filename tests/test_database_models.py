from sqlalchemy.orm import Session
from backend.app.models.crop import Crop
from backend.app.models.disease import Disease
from backend.app.models.chemical import ActiveIngredient, BaseTreatment
from backend.app.models.merchant import Merchant, Product
from backend.app.models.incompatibility import ChemicalIncompatibility


def test_crops_and_diseases_relationship(db_session: Session):
    """Verifies relational integrity between Crops and Diseases."""
    tomato = db_session.query(Crop).filter(Crop.name == "Tomato").first()
    assert tomato is not None
    assert len(tomato.diseases) >= 2


def test_base_treatments_and_active_ingredients(db_session: Session):
    """Verifies that base treatments link to valid active ingredients and have positive dosages."""
    treatments = db_session.query(BaseTreatment).all()
    assert len(treatments) > 0

    for t in treatments:
        assert t.base_dose_D0 > 0.0
        assert t.dose_unit in ["kg/acre", "g/acre", "L/acre", "mL/acre"]
        assert t.active_ingredient is not None
        assert t.active_ingredient.standard_concentration_Cr > 0.0
        assert t.active_ingredient.max_legal_dose_cap >= t.base_dose_D0


def test_merchant_product_relationships(db_session: Session):
    """Verifies that merchants possess products and prices are positive."""
    merchants = db_session.query(Merchant).all()
    assert len(merchants) >= 3

    for m in merchants:
        assert len(m.products) > 0
        for p in m.products:
            assert p.price > 0.0
            assert p.concentration_Cs > 0.0
            assert p.stock_quantity >= 0
            assert p.is_legally_registered is True


def test_chemical_incompatibilities(db_session: Session):
    """Verifies chemical incompatibilities table stores pairs with warning messages."""
    incompatibilities = db_session.query(ChemicalIncompatibility).all()
    assert len(incompatibilities) > 0

    for inc in incompatibilities:
        assert inc.ingredient_a is not None
        assert inc.ingredient_b is not None
        assert len(inc.warning_message) > 10
