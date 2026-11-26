import logging
import threading
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

from backend.app.core.config import settings
from backend.app.schemas.soil import SoilTelemetryParameters, SoilUncertaintyInfo

logger = logging.getLogger(__name__)


def round_to_grid(coordinate: float, grid_deg: float = 0.005) -> float:
    """Rounds a latitude or longitude to the nearest ~500m spatial grid cell.

    At low to mid latitudes, 0.005 degrees corresponds to approximately 500-555 meters,
    pooling localized agricultural queries and respecting SoilGrids service usage policies.
    """
    return round(round(coordinate / grid_deg) * grid_deg, 4)


class SpatialCacheEntry:
    """Represents a cached soil telemetry entry with TTL expiry."""

    def __init__(
        self,
        rounded_lat: float,
        rounded_lon: float,
        depth: str,
        parameters: SoilTelemetryParameters,
        uncertainties: Optional[Dict[str, SoilUncertaintyInfo]],
        source: str,
        created_at: datetime,
        ttl_seconds: int,
    ):
        self.rounded_lat = rounded_lat
        self.rounded_lon = rounded_lon
        self.depth = depth
        self.parameters = parameters
        self.uncertainties = uncertainties
        self.source = source
        self.created_at = created_at
        self.expires_at = created_at + timedelta(seconds=ttl_seconds)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        current_time = now or datetime.now(timezone.utc)
        return current_time >= self.expires_at


class SpatialSoilCache:
    """Thread-safe spatial cache for soil telemetry with coordinate rounding and configurable TTL."""

    def __init__(
        self,
        grid_deg: Optional[float] = None,
        default_ttl_seconds: Optional[int] = None,
    ):
        self.grid_deg = grid_deg or settings.SOILGRIDS_CACHE_GRID_SIZE_DEG
        self.default_ttl_seconds = default_ttl_seconds or settings.SOILGRIDS_CACHE_TTL_SECONDS
        self._cache: Dict[Tuple[float, float, str], SpatialCacheEntry] = {}
        self._lock = threading.Lock()

    def _make_key(self, latitude: float, longitude: float, depth: str) -> Tuple[float, float, str]:
        r_lat = round_to_grid(latitude, self.grid_deg)
        r_lon = round_to_grid(longitude, self.grid_deg)
        return (r_lat, r_lon, depth)

    def get(
        self,
        latitude: float,
        longitude: float,
        depth: str = "0-5cm",
    ) -> Optional[SpatialCacheEntry]:
        """Retrieves a valid, non-expired cache entry for the specified coordinate and depth."""
        key = self._make_key(latitude, longitude, depth)
        now = datetime.now(timezone.utc)

        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired(now):
                logger.debug("Cache entry for key %s has expired (TTL exceeded)", key)
                del self._cache[key]
                return None
            return entry

    def set(
        self,
        latitude: float,
        longitude: float,
        depth: str,
        parameters: SoilTelemetryParameters,
        uncertainties: Optional[Dict[str, SoilUncertaintyInfo]] = None,
        source: str = "ISRIC_SoilGrids_2.0",
        ttl_seconds: Optional[int] = None,
    ) -> SpatialCacheEntry:
        """Stores a soil telemetry result into the spatial cache with grid rounding and TTL."""
        key = self._make_key(latitude, longitude, depth)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        now = datetime.now(timezone.utc)

        entry = SpatialCacheEntry(
            rounded_lat=key[0],
            rounded_lon=key[1],
            depth=depth,
            parameters=parameters,
            uncertainties=uncertainties,
            source=source,
            created_at=now,
            ttl_seconds=ttl,
        )

        with self._lock:
            self._cache[key] = entry
            logger.debug("Stored spatial cache entry for key %s (TTL: %ds)", key, ttl)
        return entry

    def clear(self) -> None:
        """Clears all cached entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Returns the number of active entries currently in cache."""
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """Removes expired entries from the cache and returns the number of purged items."""
        now = datetime.now(timezone.utc)
        removed = 0
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired(now)]
            for k in expired_keys:
                del self._cache[k]
                removed += 1
        return removed


# Global singleton instance
spatial_soil_cache = SpatialSoilCache()
