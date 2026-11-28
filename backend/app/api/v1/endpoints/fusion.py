import logging
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status, Query
from backend.app.schemas.fusion import FusionRecommendationResponse
from backend.app.fusion.service import fusion_service
from backend.app.fusion.knowledge_base import AgronomicKnowledgeBase

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/recommend", response_model=FusionRecommendationResponse, summary="Multimodal Fusion & Bounded Dosage Recommendation")
async def get_fusion_recommendation(
    crop_name: str = Form(..., description="Crop common name (e.g. 'Tomato', 'Potato', 'Rice')"),
    crop_stage: str = Form(..., description="Crop phenological growth stage (e.g. 'Vegetative', 'Flowering', 'Fruiting', 'Tillering')"),
    latitude: float = Form(..., ge=-90.0, le=90.0, description="Farmer field latitude"),
    longitude: float = Form(..., ge=-180.0, le=180.0, description="Farmer field longitude"),
    days_to_harvest: Optional[int] = Form(None, ge=0, description="Estimated days until harvest (for PHI validation)"),
    co_applied_chemicals: Optional[str] = Form(None, description="Comma-separated list of co-applied tank-mix chemicals"),
    diagnosed_disease: Optional[str] = Form(None, description="Direct diagnosed disease name (if bypassing leaf photograph upload)"),
    diagnostic_confidence: Optional[float] = Form(None, ge=0.0, le=1.0, description="Direct diagnostic confidence probability"),
    allow_demo: bool = Form(False, description="Enable inclusion of unverified demonstration records (strictly for testing)"),
    image: Optional[UploadFile] = File(None, description="Optional plant leaf photograph for live vision diagnosis"),
) -> FusionRecommendationResponse:
    r"""Executes the central multimodal data fusion pipeline.

    Fuses:
    1. Vision Stream disease diagnosis and lesion-to-leaf severity ratio ($S_{severity}$).
    2. Remote Geospatial Soil Telemetry (ISRIC SoilGrids 2.0 with regional fallback).
    3. Agronomic Knowledge Base treatment guidelines.
    4. Regulatory Safety Gate:
       - Minimum diagnostic confidence ($>= 70\%$).
       - Statutory Pre-Harvest Interval (PHI) compliance.
       - Tank-mix chemical compatibility and phytotoxicity screening.
       - Traceable scientific verification status.
    5. Mathematical Dosage Formulation:
       $$D = \\min(D_0 \\times F_s \\times F_v, D_{\\text{label\\_max}})$$
    """
    image_bytes = None
    if image is not None:
        try:
            image_bytes = await image.read()
            if len(image_bytes) == 0:
                image_bytes = None
        except Exception as exc:
            logger.error("Failed to read uploaded leaf image: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read image payload: {str(exc)}",
            )

    co_applied_list = []
    if co_applied_chemicals:
        co_applied_list = [c.strip() for c in co_applied_chemicals.split(",") if c.strip()]

    try:
        response = await fusion_service.fuse_and_recommend(
            crop_name=crop_name,
            crop_stage=crop_stage,
            latitude=latitude,
            longitude=longitude,
            days_to_harvest=days_to_harvest,
            co_applied_chemicals=co_applied_list,
            image_bytes=image_bytes,
            diagnosed_disease_override=diagnosed_disease,
            diagnostic_confidence_override=diagnostic_confidence,
            allow_demo=allow_demo,
        )
        return response
    except Exception as exc:
        logger.error("Unhandled error during multimodal fusion: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multimodal fusion processing error: {str(exc)}",
        )


@router.get("/pathologies", summary="Supported Agronomic Pathologies & Verification Status")
def list_supported_pathologies() -> List[dict]:
    """Returns all crop-disease combinations currently cataloged in the knowledge base."""
    return AgronomicKnowledgeBase.get_supported_pathologies()


@router.get("/fertilizer", summary="Soil-Adjusted Crop Fertilizer Recommendation")
async def get_soil_fertilizer_recommendation(
    crop_name: str = Query(..., description="Crop name (Tomato, Potato, Rice)"),
    crop_stage: str = Query("Vegetative", description="Growth stage"),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    field_area_acres: float = Query(1.0, gt=0.0, le=1000.0),
) -> dict:
    """Computes soil-adjusted fertilizer dosage D = min(D0 * Fs, D_max) from SoilGrids/fallback."""
    from backend.app.telemetry.service import soil_telemetry_service
    from backend.app.fusion.engine import DosageCalculator

    plan = AgronomicKnowledgeBase.get_fertilizer_plan(crop=crop_name, stage=crop_stage)
    if not plan:
        raise HTTPException(status_code=404, detail=f"No fertilizer plan found for crop '{crop_name}'")

    soil_resp = await soil_telemetry_service.get_telemetry(latitude=latitude, longitude=longitude, depth="0-5cm")
    calc = DosageCalculator.compute_dosage(treatment=plan, soil_result=soil_resp)
    total_qty = round(calc.final_prescribed_dose * field_area_acres, 2)
    return {
        "crop": crop_name,
        "crop_stage": crop_stage,
        "field_area_acres": field_area_acres,
        "product_name": plan["registered_product_name"],
        "active_ingredient": plan["active_ingredient"],
        "base_dose_D0": calc.base_dose_D0,
        "soil_factor_Fs": calc.soil_factor_Fs,
        "soil_factor_status": calc.soil_factor_status,
        "final_prescribed_dose": calc.final_prescribed_dose,
        "total_field_quantity": total_qty,
        "dose_unit": calc.dose_unit,
        "application_method": plan["application_method"],
        "instructions": plan["label_restrictions"],
        "source_citation": plan["source_citation"],
        "soil_data_status": soil_resp.data_status,
    }
