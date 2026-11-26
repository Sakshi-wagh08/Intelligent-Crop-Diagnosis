from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from backend.app.db.base import Base


class Merchant(Base):
    """Local agricultural input dealer with spatial geolocation."""

    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    contact_phone = Column(String(50), nullable=False)
    contact_email = Column(String(100), nullable=True)
    address = Column(Text, nullable=False)

    # PostGIS spatial point geometry (WGS 84, SRID 4326) with R-Tree GiST indexing
    location_geom = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False
    )

    is_active = Column(Boolean, default=True, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    products = relationship(
        "Product",
        back_populates="merchant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Merchant(id={self.id}, name='{self.name}', active={self.is_active})>"


class Product(Base):
    """Commercial pesticide/fertilizer retail formulation."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    active_ingredient_id = Column(
        Integer,
        ForeignKey("active_ingredients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    brand_name = Column(String(200), nullable=False, index=True)
    concentration_Cs = Column(Float, nullable=False)  # Actual concentration Cs in retail formulation (%)
    formulation_type = Column(String(50), nullable=False)  # WP, EC, SC, SL, WG
    package_size = Column(String(50), nullable=False)  # e.g., "500 g", "1 kg", "1 L"
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    registration_number = Column(String(100), nullable=False)
    is_legally_registered = Column(Boolean, default=True, nullable=False)
    registered_crops = Column(String(250), default="Tomato, Potato, Rice", nullable=True)
    registered_diseases = Column(String(250), default="Early Blight, Late Blight, Blast", nullable=True)
    application_method = Column(String(100), default="Foliar Spray", nullable=True)
    concentration_unit = Column(String(20), default="%", nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="products")
    active_ingredient = relationship("ActiveIngredient", back_populates="products", lazy="joined")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, brand='{self.brand_name}', Cs={self.concentration_Cs}%, stock={self.stock_quantity})>"
