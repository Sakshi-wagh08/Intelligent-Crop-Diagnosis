import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings and Environment Configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    PROJECT_NAME: str = "Intelligent Crop Diagnosis and Recommendation System"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL / PostGIS Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "crop_diagnosis"
    DATABASE_URL: Optional[str] = None

    # Spatial configuration
    SPATIAL_SRID: int = 4326
    DEFAULT_MAX_SEARCH_RADIUS_KM: float = 25.0

    # ISRIC SoilGrids 2.0 API & Telemetry
    SOILGRIDS_API_BASE_URL: str = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    SOILGRIDS_TIMEOUT_SECONDS: float = 2.0
    SOILGRIDS_CACHE_TTL_SECONDS: int = 86400  # 24 hours
    SOILGRIDS_CACHE_GRID_SIZE_DEG: float = 0.005  # ~500m grid pooling
    SOILGRIDS_ENABLE_LIVE_API: bool = True

    # Vision & ML Checkpoints
    EFFICIENTNET_WEIGHTS_PATH: str = "ml_models/weights/efficientnet_b0_best.pth"
    EFFICIENTNET_ONNX_PATH: str = "ml_models/weights/efficientnet_b0.onnx"

    @property
    def get_database_url(self) -> str:
        """Construct standard database URL if not explicitly provided."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
