"""Current weather via Open-Meteo (geocoding + forecast), with retries and wttr.in fallback."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import httpx

_HEADERS = {"User-Agent": "multi-agent-tool/1.0 (weather)"}
_RETRY_STATUS = {429, 502, 503, 504}
_MAX_ATTEMPTS = 3


def _get_with_retries(client: httpx.Client, url: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            resp = client.get(url, params=params)
            if resp.status_code in _RETRY_STATUS and attempt < _MAX_ATTEMPTS - 1:
                time.sleep(0.5 * (2**attempt))
                continue
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as e:
            last_exc = e
            if e.response.status_code in _RETRY_STATUS and attempt < _MAX_ATTEMPTS - 1:
                time.sleep(0.5 * (2**attempt))
                continue
            raise
        except httpx.RequestError as e:
            last_exc = e
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(0.5 * (2**attempt))
                continue
            raise
    raise last_exc or RuntimeError("request failed")


def fetch_weather(city: str) -> str:
    city = city.strip()
    if not city:
        return "Error: city name is required"
    try:
        return _fetch_open_meteo(city)
    except Exception as open_meteo_err:
        try:
            return _fetch_wttr(city)
        except Exception:
            return (
                f"Error: could not fetch weather for '{city}'. "
                f"Open-Meteo: {open_meteo_err}. "
                "Fallback source also failed."
            )


def _fetch_open_meteo(city: str) -> str:
    with httpx.Client(timeout=25.0, headers=_HEADERS, follow_redirects=True) as client:
        geo = _get_with_retries(
            client,
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        gdata = geo.json()
        results = gdata.get("results") or []
        if not results:
            return f"No location found for '{city}'."
        r0 = results[0]
        lat, lon = r0["latitude"], r0["longitude"]
        name = r0.get("name", city)
        country = r0.get("country_code", "")
        admin = r0.get("admin1", "")
        loc = f"{name}" + (f", {admin}" if admin else "") + (f", {country}" if country else "")

        fc = _get_with_retries(
            client,
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        fdata = fc.json()
        cur = fdata.get("current") or {}
        temp = cur.get("temperature_2m")
        hum = cur.get("relative_humidity_2m")
        code = cur.get("weather_code")
        wind = cur.get("wind_speed_10m")
        unit_temp = fdata.get("current_units", {}).get("temperature_2m", "°C")
        unit_wind = fdata.get("current_units", {}).get("wind_speed_10m", "km/h")
        wmo = _wmo_label(code)
        parts = [f"Location: {loc} (Open-Meteo)."]
        if temp is not None:
            parts.append(f"Temperature: {temp}{unit_temp}.")
        if hum is not None:
            parts.append(f"Relative humidity: {hum}%.")
        if wind is not None:
            parts.append(f"Wind speed: {wind} {unit_wind}.")
        if wmo:
            parts.append(f"Conditions: {wmo}.")
        return " ".join(parts)


def _fetch_wttr(city: str) -> str:
    """Fallback when Open-Meteo is down (502, etc.)."""
    url = f"https://wttr.in/{quote(city)}?format=j1"
    with httpx.Client(timeout=25.0, headers={**_HEADERS, "Accept": "application/json"}) as client:
        resp = _get_with_retries(client, url)
        data = resp.json()
        area = data.get("nearest_area", [{}])
        area0 = area[0] if area else {}
        place = area0.get("areaName", [{}])
        place_name = place[0].get("value", city) if place else city
        country = area0.get("country", [{}])
        country_name = country[0].get("value", "") if country else ""
        loc = f"{place_name}" + (f", {country_name}" if country_name else "")

        current = (data.get("current_condition") or [{}])[0]
        temp = current.get("temp_C")
        hum = current.get("humidity")
        wind = current.get("windspeedKmph")
        desc_list = current.get("weatherDesc") or []
        desc = desc_list[0].get("value", "") if desc_list else ""

        parts = [f"Location: {loc} (wttr.in fallback)."]
        if temp is not None:
            parts.append(f"Temperature: {temp}°C.")
        if hum is not None:
            parts.append(f"Relative humidity: {hum}%.")
        if wind is not None:
            parts.append(f"Wind speed: {wind} km/h.")
        if desc:
            parts.append(f"Conditions: {desc}.")
        return " ".join(parts)


def _wmo_label(code: int | None) -> str:
    if code is None:
        return ""
    table = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return table.get(int(code), f"Code {code}")


def weather_openai_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "Get current weather conditions for a city or town name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, e.g. 'Tokyo' or 'Paris, France'.",
                    }
                },
                "required": ["city"],
            },
        },
    }
