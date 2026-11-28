"""Lightweight Spray-Window Weather Advisory Client (Open-Meteo).

Provides real-time rain and wind checks for safe foliar spraying without requiring
an API key. Degrades gracefully when offline or timed out.
"""

import asyncio
import logging
import socket
import threading
import time
from typing import Dict, Any, Tuple
import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_HOST = "api.open-meteo.com"
OPEN_METEO_URL = f"https://{OPEN_METEO_HOST}/v1/forecast"
WEATHER_TIMEOUT_SECONDS = 1.2
WEATHER_CACHE_TTL_SECONDS = 600  # 10 minutes
_WEATHER_CACHE: Dict[Tuple[float, float], Tuple[float, Dict[str, Any]]] = {}


async def _is_host_resolvable_async(host: str, timeout: float = 0.6) -> bool:
    """Checks DNS resolution in a daemon thread without blocking the event loop or executor shutdown."""
    loop = asyncio.get_running_loop()
    done = asyncio.Event()
    resolved = False

    def _probe():
        nonlocal resolved
        try:
            socket.getaddrinfo(host, 443)
            resolved = True
        except OSError:
            resolved = False
        finally:
            try:
                loop.call_soon_threadsafe(done.set)
            except RuntimeError:
                pass

    threading.Thread(target=_probe, daemon=True).start()
    try:
        await asyncio.wait_for(done.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        return False
    return resolved


async def get_spray_weather_advisory(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetches current temperature, wind speed, and next-4h rain forecast via Open-Meteo."""
    cache_key = (round(latitude, 2), round(longitude, 2))
    cached = _WEATHER_CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < WEATHER_CACHE_TTL_SECONDS:
        return dict(cached[1])

    params = {
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "current": "temperature_2m,precipitation,wind_speed_10m",
        "hourly": "precipitation_probability,precipitation,wind_speed_10m",
        "forecast_days": 1,
        "timezone": "auto",
    }

    try:
        if not await _is_host_resolvable_async(OPEN_METEO_HOST, 0.6):
            raise ConnectionError("Weather host unreachable or offline")

        async with httpx.AsyncClient(timeout=WEATHER_TIMEOUT_SECONDS) as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})

        temp_c = current.get("temperature_2m")
        wind_kmh = current.get("wind_speed_10m")
        current_precip_mm = current.get("precipitation", 0.0) or 0.0

        # Inspect next few hourly slots for rain risk within 4 hours
        probs = hourly.get("precipitation_probability") or []
        precips = hourly.get("precipitation") or []
        next_4h_rain_prob = max([p for p in probs[:5] if p is not None], default=0)
        next_4h_precip_mm = max([p for p in precips[:5] if p is not None], default=0.0)

        wind_high = wind_kmh is not None and float(wind_kmh) > 15.0
        rain_risk = (
            float(current_precip_mm) > 0.2
            or float(next_4h_precip_mm) > 0.5
            or float(next_4h_rain_prob) >= 50.0
        )

        if wind_high and rain_risk:
            is_good = False
            advisory = (
                f"Wait before spraying: strong wind ({wind_kmh} km/h) and rain risk "
                f"({next_4h_rain_prob}% chance) in the next 4 hours."
            )
        elif wind_high:
            is_good = False
            advisory = (
                f"Wait before spraying: wind is {wind_kmh} km/h (above the 15 km/h safe spray limit, "
                "which causes chemical drift)."
            )
        elif rain_risk:
            is_good = False
            advisory = (
                f"Wait before spraying: rain expected within 4 hours ({next_4h_rain_prob}% chance), "
                "which can wash off the spray."
            )
        else:
            is_good = True
            advisory = (
                f"Good weather to spray now: calm wind ({wind_kmh if wind_kmh is not None else 'low'} km/h) "
                "and low rain risk over the next 4 hours."
            )

        result = {
            "weather_status": "live",
            "is_good_to_spray": is_good,
            "temperature_c": temp_c,
            "wind_speed_kmh": wind_kmh,
            "rain_probability_next_4h": next_4h_rain_prob,
            "advisory": advisory,
            "source": "Open-Meteo Live Weather",
        }
        _WEATHER_CACHE[cache_key] = (time.time(), result)
        return dict(result)
    except Exception as exc:
        logger.info("Weather check unavailable (%s); returning offline advisory.", exc)
        fallback = {
            "weather_status": "unavailable",
            "is_good_to_spray": None,
            "temperature_c": None,
            "wind_speed_kmh": None,
            "rain_probability_next_4h": None,
            "advisory": (
                "Live weather unavailable offline. Check the sky: do not spray if it is windy "
                "(>15 km/h) or if rain is expected within 4 hours."
            ),
            "source": "Offline Safety Check",
        }
        _WEATHER_CACHE[cache_key] = (time.time(), fallback)
        return dict(fallback)
