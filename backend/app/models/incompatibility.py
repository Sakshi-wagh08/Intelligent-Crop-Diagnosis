from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


class ChemicalIncompatibility(Base):
    """Prohibited agrochemical mixtures and phytotoxicity warnings."""

    __tablename__ = "chemical_incompatibilities"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_a_id = Column(
        Integer,
        ForeignKey("active_ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ingredient_b_id = Column(
        Integer,
        ForeignKey("active_ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    warning_message = Column(Text, nullable=False)
    incompatibility_type = Column(
        String(50),
        default="Tank-mix phytotoxicity hazard",
        nullable=False
    )
    is_demo = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("ingredient_a_id", "ingredient_b_id", name="uq_incompatibility_pair"),
    )

    # Relationships
    ingredient_a = relationship("ActiveIngredient", foreign_keys=[ingredient_a_id])
    ingredient_b = relationship("ActiveIngredient", foreign_keys=[ingredient_b_id])

    def __repr__(self) -> str:
        return f"<ChemicalIncompatibility({self.ingredient_a_id} <-> {self.ingredient_b_id})>"
