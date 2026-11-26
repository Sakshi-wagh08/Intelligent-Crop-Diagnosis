from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status
from backend.app.schemas.vision import VisionDiagnosisResponse, VisionStatusResponse
from backend.app.vision.service import vision_service
from backend.app.vision.model import DEFAULT_SUPPORTED_CLASSES
from backend.app.vision.exceptions import (
    InvalidImageError,
    ImageTooLargeError,
    CorruptImageError,
    VisionError,
)

router = APIRouter()


@router.get("/status", response_model=VisionStatusResponse, summary="Query Vision Stream Operational Status")
def get_vision_status() -> VisionStatusResponse:
    """Returns the initialization status of PyTorch and ONNX classifiers, and supported classes."""
    return VisionStatusResponse(
        has_active_model=vision_service.has_active_model,
        pytorch_loaded=(
            vision_service.pytorch_classifier is not None and
            vision_service.pytorch_classifier.is_loaded
        ),
        onnx_loaded=(
            vision_service.onnx_classifier is not None and
            vision_service.onnx_classifier.is_loaded
        ),
        supported_classes=DEFAULT_SUPPORTED_CLASSES,
        pytorch_weights_path=vision_service.pytorch_weights_path,
        onnx_weights_path=vision_service.onnx_weights_path,
    )


@router.post(
    "/diagnose",
    response_model=VisionDiagnosisResponse,
    summary="Plant Leaf Image Diagnosis & Severity Estimation"
)
async def diagnose_leaf_image(
    file: UploadFile = File(..., description="Uploaded leaf photograph (JPEG, PNG, WEBP)"),
    top_k: int = Query(3, ge=1, le=10, description="Number of top predictions to return")
) -> VisionDiagnosisResponse:
    """Processes an uploaded leaf photograph to estimate disease severity and detect pathology.

    Phase 2 Specification:
    - Performs file validation and orientation correction.
    - Estimates lesion-to-leaf surface area ratio (S_severity) via OpenCV segmentation.
    - Runs disease classification if trained weights are available; otherwise returns
      an informative status without fabricating predictions.
    - Does NOT link to dosage or merchant substitution in this phase.
    """
    try:
        content = await file.read()
        result = vision_service.diagnose_image(content, top_k=top_k)
        return VisionDiagnosisResponse(**result)
    except (InvalidImageError, ImageTooLargeError, CorruptImageError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
    except VisionError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision stream error: {err}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error processing leaf image: {exc}"
        )
