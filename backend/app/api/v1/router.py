from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, crops, merchants, soil, vision, fusion

api_router = APIRouter()

api_router.include_router(health.router, tags=["System Health & Diagnostics"])
api_router.include_router(vision.router, prefix="/vision", tags=["Vision Stream - Plant Disease Detection"])
api_router.include_router(crops.router, prefix="/crops", tags=["Agronomic Crops & Pathologies"])
api_router.include_router(merchants.router, prefix="/merchants", tags=["Localized Merchant Spatial Search"])
api_router.include_router(soil.router, prefix="/soil", tags=["Remote Geospatial Soil Telemetry"])
api_router.include_router(fusion.router, prefix="/fusion", tags=["Multimodal Fusion & Recommendation Engine"])
