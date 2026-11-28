from fastapi import APIRouter
from backend.app.schemas.health import HealthResponse
from backend.app.db.session import check_database_connection, check_postgis_extension, database_url
from backend.app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System Health & PostGIS Diagnostic Probe")
def get_health() -> HealthResponse:
    """Probes the application health status, database connectivity, and PostGIS spatial extension."""
    db_connected, db_error = check_database_connection()
    postgis_enabled, postgis_version = check_postgis_extension()

    if db_connected and postgis_enabled:
        overall_status = "healthy"
    elif db_connected and not postgis_enabled:
        overall_status = "degraded (database connected, but PostGIS extension missing)"
    else:
        overall_status = "degraded (database offline or unreachable)"

    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database={
            "connected": db_connected,
            "postgis_enabled": postgis_enabled,
            "postgis_version_or_status": postgis_version if postgis_enabled else (db_error or "Unavailable"),
            "dialect": database_url.split(":")[0],
            "target_host": settings.POSTGRES_HOST,
            "target_port": settings.POSTGRES_PORT,
            "target_db": settings.POSTGRES_DB
        },
        components={
            "vision_engine": "EfficientNet-B0 (Architecture Stage: Phase 2 planned)",
            "soilgrids_client": "ISRIC SoilGrids 2.0 Telemetry Interface Ready",
            "spatial_radius_search": "PostGIS GiST Index SRID 4326 Configured"
        }
    )
