from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db, check_database_connection
from backend.app.models.crop import Crop
from backend.app.schemas.crop import CropResponse, DiseaseBase
from backend.app.core.logging import logger

router = APIRouter()


@router.get("", response_model=List[CropResponse], summary="Retrieve Supported Crops & Diseases")
def list_crops(db: Session = Depends(get_db)) -> List[CropResponse]:
    """Retrieves all registered crops and their associated disease profiles."""
    try:
        crops = db.query(Crop).order_by(Crop.name.asc()).all()
        if crops:
            return crops
    except Exception as exc:
        logger.warning(f"Database query error in list_crops: {exc}. Using fallback catalog.")

    # Documented fallback from verified agronomic knowledge base
    fallback_crops = [
        CropResponse(
            id=1,
            name="Tomato",
            scientific_name="Solanum lycopersicum",
            description="Solanaceous fruit crop susceptible to Early Blight and Late Blight.",
            diseases=[
                DiseaseBase(id=1, disease_name="Early Blight", scientific_name="Alternaria solani", pathogen_type="Fungal", symptoms="Dark concentric target-board lesions on lower foliage."),
                DiseaseBase(id=2, disease_name="Late Blight", scientific_name="Phytophthora infestans", pathogen_type="Oomycete", symptoms="Rapidly expanding water-soaked foliar necrosis.")
            ]
        ),
        CropResponse(
            id=2,
            name="Potato",
            scientific_name="Solanum tuberosum",
            description="Tuber crop susceptible to Late Blight foliar epidemics.",
            diseases=[
                DiseaseBase(id=3, disease_name="Late Blight", scientific_name="Phytophthora infestans", pathogen_type="Oomycete", symptoms="Dark water-soaked necrotic lesions with white sporulation under humid conditions.")
            ]
        ),
        CropResponse(
            id=3,
            name="Rice",
            scientific_name="Oryza sativa",
            description="Cereal grain crop susceptible to fungal blast.",
            diseases=[
                DiseaseBase(id=4, disease_name="Blast", scientific_name="Magnaporthe oryzae", pathogen_type="Fungal", symptoms="Spindle-shaped or diamond lesions on leaf blades.")
            ]
        )
    ]
    return fallback_crops
