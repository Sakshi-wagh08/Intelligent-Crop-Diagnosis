import logging
from fastapi import APIRouter, Query, HTTPException, status
from backend.app.schemas.soil import SoilTelemetryResponse
from backend.app.telemetry.service import soil_telemetry_service
from backend.app.telemetry.exceptions import InvalidCoordinatesError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/telemetry", response_model=SoilTelemetryResponse, summary="Query Geospatial Soil Telemetry")
async def get_soil_telemetry(
    latitude: float = Query(
        ...,
        ge=-90.0,
        le=90.0,
        description="Farmer field latitude in decimal degrees (-90.0 to 90.0)",
    ),
    longitude: float = Query(
        ...,
        ge=-180.0,
        le=180.0,
        description="Farmer field longitude in decimal degrees (-180.0 to 180.0)",
    ),
    depth: str = Query(
        "0-5cm",
        description="Target soil depth horizon interval (default: '0-5cm')",
    ),
) -> SoilTelemetryResponse:
    """Queries geospatial soil telemetry for given field coordinates.

    Executes a resilient, multi-tiered retrieval pipeline:
    1. Coordinate Validation (WGS-84 bounds).
    2. Spatial Cache Check (~500m grid pooling with configurable TTL).
    3. ISRIC SoilGrids 2.0 RESTful Spatial API asynchronous query.
    4. Unit conversion, quantile extraction, and USDA soil texture classification.
    5. Automatic regional agronomic benchmark fallback (ICAR-NBSS&LUP) on service timeout or masked terrain.
    6. Explicit 'unavailable' status when outside regional benchmark coverage (prevention of fabricated values).
    """
    try:
        response = await soil_telemetry_service.get_telemetry(
            latitude=latitude,
            longitude=longitude,
            depth=depth,
        )
        return response
    except InvalidCoordinatesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unhandled error in soil telemetry endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal soil telemetry processing error: {str(exc)}",
        )
