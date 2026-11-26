"""Domain exceptions for Soil Telemetry and ISRIC SoilGrids Integration."""


class SoilTelemetryError(Exception):
    """Base exception for all soil telemetry operations."""
    pass


class InvalidCoordinatesError(SoilTelemetryError):
    """Raised when latitude or longitude falls outside valid WGS-84 coordinate bounds."""
    def __init__(self, latitude: float, longitude: float, message: str = None):
        self.latitude = latitude
        self.longitude = longitude
        super().__init__(
            message or f"Invalid coordinates ({latitude}, {longitude}): latitude must be [-90, 90] and longitude [-180, 180]"
        )


class SoilGridsAPIError(SoilTelemetryError):
    """Raised when the external ISRIC SoilGrids API returns an error response or connection fails."""
    def __init__(self, status_code: int = None, details: str = None):
        self.status_code = status_code
        self.details = details
        super().__init__(f"SoilGrids API error (status {status_code}): {details}")


class SoilGridsTimeoutError(SoilTelemetryError):
    """Raised when the SoilGrids API query exceeds the configured timeout threshold."""
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"SoilGrids API request timed out after {timeout_seconds:.1f}s")


class SoilDataUnavailableError(SoilTelemetryError):
    """Raised when no live, cached, or regional fallback soil telemetry is available for the given location."""
    def __init__(self, latitude: float, longitude: float, reason: str = "External service unavailable and no regional fallback"):
        self.latitude = latitude
        self.longitude = longitude
        self.reason = reason
        super().__init__(f"Soil telemetry unavailable for ({latitude}, {longitude}): {reason}")
