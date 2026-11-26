import logging
from typing import Dict, Any, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.telemetry.exceptions import (
    SoilGridsAPIError,
    SoilGridsTimeoutError,
    InvalidCoordinatesError,
)

logger = logging.getLogger(__name__)

# Verified soil properties accessible via ISRIC SoilGrids 2.0 RESTful API
SUPPORTED_PROPERTIES: List[str] = [
    "phh2o",      # Soil pH in H2O
    "soc",        # Soil organic carbon
    "nitrogen",   # Total nitrogen
    "cec",        # Cation exchange capacity at pH 7
    "sand",       # Sand fraction (0.05 - 2 mm)
    "silt",       # Silt fraction (0.002 - 0.05 mm)
    "clay",       # Clay fraction (< 0.002 mm)
    "wv0010",     # Volumetric water content at 10 kPa
    "wv0033",     # Volumetric water content at 33 kPa (field capacity)
    "wv1500",     # Volumetric water content at 1500 kPa (permanent wilting point)
]

SUPPORTED_DEPTHS: List[str] = [
    "0-5cm",
    "5-15cm",
    "15-30cm",
    "30-60cm",
    "60-100cm",
    "100-200cm",
]

SUPPORTED_VALUES: List[str] = [
    "mean",
    "Q0.05",
    "Q0.5",
    "Q0.95",
    "uncertainty",
]


class SoilGridsClient:
    """Asynchronous HTTP client for the official ISRIC SoilGrids 2.0 RESTful API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.base_url = base_url or settings.SOILGRIDS_API_BASE_URL
        self.timeout_seconds = timeout_seconds or settings.SOILGRIDS_TIMEOUT_SECONDS

    def validate_coordinates(self, latitude: float, longitude: float) -> None:
        """Validates that coordinates conform to WGS-84 coordinate bounds."""
        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            raise InvalidCoordinatesError(latitude, longitude)

    async def query_properties(
        self,
        latitude: float,
        longitude: float,
        depth: str = "0-5cm",
        properties: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Queries SoilGrids 2.0 REST API for specified soil layers at given coordinates and depth.

        Args:
            latitude: Latitude in decimal degrees (-90.0 to 90.0).
            longitude: Longitude in decimal degrees (-180.0 to 180.0).
            depth: Soil depth interval (default: '0-5cm').
            properties: Subset of supported properties to query (defaults to all supported).

        Returns:
            Raw dictionary containing layers, unit measures, and values parsed from SoilGrids GeoJSON.

        Raises:
            InvalidCoordinatesError: If coordinates are out of bounds.
            SoilGridsTimeoutError: If external API call exceeds timeout threshold.
            SoilGridsAPIError: On HTTP error response, connection drop, or invalid JSON.
        """
        self.validate_coordinates(latitude, longitude)

        if depth not in SUPPORTED_DEPTHS:
            logger.warning("Requested depth '%s' not in standard SoilGrids depths, defaulting to '0-5cm'", depth)
            depth = "0-5cm"

        query_props = properties or SUPPORTED_PROPERTIES

        # Construct multi-valued query parameters according to SoilGrids 2.0 REST specification
        query_params: List[tuple] = [
            ("lat", str(latitude)),
            ("lon", str(longitude)),
            ("depth", depth),
        ]
        for prop in query_props:
            query_params.append(("property", prop))
        for val in SUPPORTED_VALUES:
            query_params.append(("value", val))

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.base_url, params=query_params)

                if response.status_code == 422:
                    raise SoilGridsAPIError(
                        status_code=422,
                        details=f"Unprocessable entity from SoilGrids: {response.text}",
                    )

                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as exc:
            logger.warning(
                "SoilGrids request timed out after %.2fs for (%s, %s): %s",
                self.timeout_seconds, latitude, longitude, exc
            )
            raise SoilGridsTimeoutError(timeout_seconds=self.timeout_seconds) from exc

        except httpx.HTTPStatusError as exc:
            logger.error("SoilGrids HTTP %d error: %s", exc.response.status_code, exc.response.text)
            raise SoilGridsAPIError(
                status_code=exc.response.status_code,
                details=exc.response.text,
            ) from exc

        except httpx.RequestError as exc:
            logger.error("SoilGrids connection/transport error: %s", exc)
            raise SoilGridsAPIError(
                status_code=None,
                details=f"Transport connection error: {str(exc)}",
            ) from exc

        except Exception as exc:
            logger.error("Unexpected error querying SoilGrids API: %s", exc)
            raise SoilGridsAPIError(
                status_code=None,
                details=f"Unexpected parsing/processing error: {str(exc)}",
            ) from exc

        # Validate GeoJSON structure
        if not isinstance(data, dict) or "properties" not in data:
            raise SoilGridsAPIError(
                status_code=200,
                details="Malformed SoilGrids response: missing 'properties' dictionary",
            )

        layers = data.get("properties", {}).get("layers", [])
        return {
            "latitude": latitude,
            "longitude": longitude,
            "depth": depth,
            "layers": layers,
            "query_time_s": data.get("query_time_s"),
        }
