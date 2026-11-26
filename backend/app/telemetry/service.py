import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.schemas.soil import (
    SoilTelemetryResponse,
    SoilTelemetryParameters,
)
from backend.app.telemetry.exceptions import (
    InvalidCoordinatesError,
    SoilGridsAPIError,
    SoilGridsTimeoutError,
)
from backend.app.telemetry.soilgrids import SoilGridsClient
from backend.app.telemetry.processing import (
    validate_wgs84_coordinates,
    process_soilgrids_layers,
    STANDARD_UNITS,
    DISCLAIMER_MODELED_ESTIMATE,
)
from backend.app.telemetry.cache import spatial_soil_cache, SpatialSoilCache
from backend.app.telemetry.fallback import RegionalSoilFallback

logger = logging.getLogger(__name__)


class SoilTelemetryService:
    """Orchestrates soil telemetry acquisition, caching, processing, and fallback handling."""

    def __init__(
        self,
        soilgrids_client: Optional[SoilGridsClient] = None,
        cache: Optional[SpatialSoilCache] = None,
    ):
        self.client = soilgrids_client or SoilGridsClient()
        self.cache = cache or spatial_soil_cache

    async def get_telemetry(
        self,
        latitude: float,
        longitude: float,
        depth: str = "0-5cm",
    ) -> SoilTelemetryResponse:
        """Retrieves soil telemetry for given coordinates, checking cache, live API, and fallback.

        Execution Pipeline:
        1. Coordinate validation (WGS-84).
        2. Spatial Cache check (~500m grid pooling).
        3. External ISRIC SoilGrids 2.0 RESTful API call with timeout protection.
        4. Processing & Unit conversions.
        5. Regional Agronomic Benchmark fallback if external service fails or returns masked nulls.
        6. Explicit Unavailable status if outside all documented regional benchmark zones.
        """
        # Step 1: Validate coordinates
        validate_wgs84_coordinates(latitude, longitude)

        # Step 2: Check Spatial Cache
        cached_entry = self.cache.get(latitude, longitude, depth)
        if cached_entry is not None:
            logger.info("Serving soil telemetry from spatial cache for (%s, %s)", latitude, longitude)
            is_fallback = cached_entry.source.startswith("Regional_Agronomic_Fallback")
            data_status = "cached"
            advisory = (
                cached_entry.source if is_fallback else DISCLAIMER_MODELED_ESTIMATE
            )

            return SoilTelemetryResponse(
                latitude=latitude,
                longitude=longitude,
                depth=depth,
                telemetry_source=f"Spatial_Cache ({cached_entry.source})",
                data_status=data_status,
                is_fallback=is_fallback,
                retrieval_timestamp=cached_entry.created_at.isoformat(),
                parameters=cached_entry.parameters,
                units=STANDARD_UNITS,
                uncertainty_level="Cached Modeled Estimate (~500m spatial pool)",
                uncertainty_quantiles=cached_entry.uncertainties,
                advisory_notice=advisory,
            )

        # Step 3: Attempt Live SoilGrids 2.0 Fetch
        live_parameters: Optional[SoilTelemetryParameters] = None
        uncertainties = None
        live_failed_reason: Optional[str] = None

        if settings.SOILGRIDS_ENABLE_LIVE_API:
            try:
                raw_data = await self.client.query_properties(latitude, longitude, depth)
                live_parameters, uncertainties = process_soilgrids_layers(raw_data, depth)

                if live_parameters is not None:
                    # Valid live data retrieved successfully
                    self.cache.set(
                        latitude=latitude,
                        longitude=longitude,
                        depth=depth,
                        parameters=live_parameters,
                        uncertainties=uncertainties,
                        source="ISRIC_SoilGrids_2.0",
                    )
                    now_iso = datetime.now(timezone.utc).isoformat()
                    return SoilTelemetryResponse(
                        latitude=latitude,
                        longitude=longitude,
                        depth=depth,
                        telemetry_source="ISRIC_SoilGrids_2.0",
                        data_status="live",
                        is_fallback=False,
                        retrieval_timestamp=now_iso,
                        parameters=live_parameters,
                        units=STANDARD_UNITS,
                        uncertainty_level="Modeled Estimate (250m gridded resolution)",
                        uncertainty_quantiles=uncertainties,
                        advisory_notice=DISCLAIMER_MODELED_ESTIMATE,
                    )
                else:
                    live_failed_reason = "SoilGrids returned null values for all requested layers (masked/water terrain)"
                    logger.warning("SoilGrids returned nulls for (%s, %s): %s", latitude, longitude, live_failed_reason)

            except (SoilGridsTimeoutError, SoilGridsAPIError) as exc:
                live_failed_reason = str(exc)
                logger.warning("SoilGrids live query failed for (%s, %s): %s", latitude, longitude, exc)

            except Exception as exc:
                live_failed_reason = f"Unexpected live fetch exception: {str(exc)}"
                logger.error("Unexpected live soil fetch failure: %s", exc)
        else:
            live_failed_reason = "Live SoilGrids API query disabled by configuration"

        # Step 4: Fallback to Documented Regional Benchmarks
        fallback_params, source_desc, fallback_advisory = RegionalSoilFallback.get_fallback_telemetry(
            latitude, longitude
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        if fallback_params is not None and source_desc is not None:
            # Store fallback result in cache so subsequent nearby requests do not wait for timeout
            self.cache.set(
                latitude=latitude,
                longitude=longitude,
                depth=depth,
                parameters=fallback_params,
                uncertainties=None,
                source=source_desc,
            )

            return SoilTelemetryResponse(
                latitude=latitude,
                longitude=longitude,
                depth=depth,
                telemetry_source=source_desc,
                data_status="fallback",
                is_fallback=True,
                retrieval_timestamp=now_iso,
                parameters=fallback_params,
                units=STANDARD_UNITS,
                uncertainty_level="Regional Macro-Agroclimatic Benchmark",
                uncertainty_quantiles=None,
                advisory_notice=fallback_advisory or DISCLAIMER_MODELED_ESTIMATE,
            )

        # Step 5: Explicit Unavailable Status (No fake data allowed)
        return SoilTelemetryResponse(
            latitude=latitude,
            longitude=longitude,
            depth=depth,
            telemetry_source="Unavailable",
            data_status="unavailable",
            is_fallback=True,
            retrieval_timestamp=now_iso,
            parameters=None,
            units=STANDARD_UNITS,
            uncertainty_level="Data Unavailable",
            uncertainty_quantiles=None,
            advisory_notice=(
                f"SOIL TELEMETRY UNAVAILABLE: External ISRIC SoilGrids service could not provide data ({live_failed_reason}) "
                f"and coordinates ({latitude}, {longitude}) fall outside documented regional benchmark zones. "
                "In compliance with safety standards, no artificial or unverified soil values were generated. "
                "Laboratory soil testing or local agricultural extension verification is recommended."
            ),
        )


# Global singleton service instance
soil_telemetry_service = SoilTelemetryService()
