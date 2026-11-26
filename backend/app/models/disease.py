from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


class Disease(Base):
    """Crop pathology entity (fungal, bacterial, viral, deficiency, pest)."""

    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(
        Integer,
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    disease_name = Column(String(150), nullable=False, index=True)
    scientific_name = Column(String(200), nullable=True)
    pathogen_type = Column(String(50), nullable=False)  # Fungal, Bacterial, Viral, Deficiency, Pest
    symptoms = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("crop_id", "disease_name", name="uq_crop_disease"),
    )

    # Relationships
    crop = relationship("Crop", back_populates="diseases")
    treatments = relationship(
        "BaseTreatment",
        back_populates="disease",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Disease(id={self.id}, crop_id={self.crop_id}, name='{self.disease_name}')>"
