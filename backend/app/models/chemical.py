from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


class ActiveIngredient(Base):
    """Regulated active chemical ingredient entity."""

    __tablename__ = "active_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    common_name = Column(String(150), unique=True, nullable=False, index=True)
    chemical_family = Column(String(100), nullable=True)
    standard_concentration_Cr = Column(Float, nullable=False)  # Baseline reference concentration Cr (%)
    concentration_unit = Column(String(20), default="%", nullable=False)
    max_legal_dose_cap = Column(Float, nullable=False)  # Regulatory maximum dose per acre (D_label_max)
    phi_days = Column(Integer, default=0, nullable=False)  # Pre-Harvest Interval (days)
    ppe_requirements = Column(Text, nullable=True)  # Personal Protective Equipment directives
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    base_treatments = relationship("BaseTreatment", back_populates="active_ingredient")
    products = relationship("Product", back_populates="active_ingredient")

    def __repr__(self) -> str:
        return f"<ActiveIngredient(id={self.id}, name='{self.common_name}', Cr={self.standard_concentration_Cr})>"


class BaseTreatment(Base):
    """Agronomic package-of-practices base treatment guideline."""

    __tablename__ = "base_treatments"

    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(
        Integer,
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    active_ingredient_id = Column(
        Integer,
        ForeignKey("active_ingredients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    crop_stage = Column(String(50), nullable=False)  # Vegetative, Flowering, Fruiting, etc.
    base_dose_D0 = Column(Float, nullable=False)  # Baseline recommended dose D0 per acre
    dose_unit = Column(String(30), nullable=False)  # kg/acre, g/acre, mL/acre, L/acre
    water_dilution_liters_per_acre = Column(Float, default=200.0, nullable=False)
    application_method = Column(String(100), default="Foliar Spray", nullable=False)
    application_timing = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    disease = relationship("Disease", back_populates="treatments")
    active_ingredient = relationship("ActiveIngredient", back_populates="base_treatments", lazy="joined")

    def __repr__(self) -> str:
        return f"<BaseTreatment(id={self.id}, disease_id={self.disease_id}, D0={self.base_dose_D0} {self.dose_unit})>"
