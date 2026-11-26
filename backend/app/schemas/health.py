from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System and infrastructure health status response schema."""

    status: str = Field(..., description="Overall service status: healthy, degraded, or unhealthy")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    database: Dict[str, Any] = Field(..., description="Database connectivity and PostGIS status")
    components: Dict[str, str] = Field(default_factory=dict, description="Status of auxiliary subsystems")
