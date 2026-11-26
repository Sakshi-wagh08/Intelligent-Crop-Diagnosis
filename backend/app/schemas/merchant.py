from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductResponse(BaseModel):
    """Commercial product retail offering schema."""
    id: int
    brand_name: str
    active_ingredient_name: Optional[str] = None
    concentration_Cs: float
    concentration_unit: Optional[str] = "%"
    formulation_type: str
    package_size: str
    price: float
    currency: str
    stock_quantity: int
    registration_number: str
    is_legally_registered: bool
    registered_crops: Optional[str] = None
    registered_diseases: Optional[str] = None
    application_method: Optional[str] = "Foliar Spray"
    is_demo: bool

    model_config = ConfigDict(from_attributes=True)


class MerchantResponse(BaseModel):
    """Agro-dealer profile with stocked products."""
    id: int
    name: str
    contact_phone: str
    contact_email: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    is_active: bool
    is_demo: bool
    products: List[ProductResponse] = []

    model_config = ConfigDict(from_attributes=True)


class NearbyMerchantResponse(BaseModel):
    """Spatial dealer search result with computed distance."""
    merchant_id: int
    merchant_name: str
    contact_phone: str
    address: str
    distance_km: float = Field(..., description="Calculated geodetic distance from farmer location in kilometers")
    product_id: Optional[int] = None
    brand_name: Optional[str] = None
    concentration_Cs: Optional[float] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    is_demo: bool = True
