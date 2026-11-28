from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.session import (
    check_database_connection,
    check_postgis_extension,
    ensure_local_database_seeded,
)
from backend.app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup diagnostics and graceful shutdown."""
    logger.info("Initializing Intelligent Crop Diagnosis Application...")
    logger.info(f"Target Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database Target: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

    ensure_local_database_seeded()

    # Startup Diagnostic Checks
    db_ok, db_err = check_database_connection()
    if db_ok:
        logger.info("Database connection established successfully.")
        gis_ok, gis_ver = check_postgis_extension()
        if gis_ok:
            logger.info(f"PostGIS Spatial Extension verified: {gis_ver}")
        else:
            logger.warning(
                f"Database connected, but PostGIS extension not active: {gis_ver}. "
                "Spatial operations will run via fallback calculator until PostGIS extension is installed."
            )
    else:
        logger.warning(
            f"Database server is currently offline or unreachable: {db_err}. "
            "Please ensure PostgreSQL/PostGIS is running or started via 'docker compose up -d'."
        )

    yield

    logger.info("Shutting down Intelligent Crop Diagnosis Application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Backend API Gateway for Intelligent Crop Diagnosis and Fertilizer/Pesticide "
        "Dosage Recommendation System with Dynamic Localized Merchant Substitution. "
        "Compliant with IEEE Multimodal Precision Agriculture Specifications."
    ),
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) Middleware for PWA Client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restricted in production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API V1 Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", summary="Root Health Check & Documentation Index")
def root_index():
    """Provides project metadata and navigation to interactive OpenAPI documentation."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": f"{settings.API_V1_PREFIX}/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
