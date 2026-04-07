"""Current weather via Open-Meteo (geocoding + forecast, no API key)."""

import httpx


async def fetch_weather(city: str) -> str:
    city = city.strip()
    if not city:
        return "Error: city name is required"
    async with httpx.AsyncClient(timeout=20.0) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        geo.raise_for_status()
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

        fc = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        fc.raise_for_status()
        fdata = fc.json()
        cur = fdata.get("current") or {}
        temp = cur.get("temperature_2m")
        hum = cur.get("relative_humidity_2m")
        code = cur.get("weather_code")
        wind = cur.get("wind_speed_10m")
        unit_temp = fdata.get("current_units", {}).get("temperature_2m", "°C")
        unit_wind = fdata.get("current_units", {}).get("wind_speed_10m", "km/h")
        wmo = _wmo_label(code)
        parts = [f"Location: {loc}."]
        if temp is not None:
            parts.append(f"Temperature: {temp}{unit_temp}.")
        if hum is not None:
            parts.append(f"Relative humidity: {hum}%.")
        if wind is not None:
            parts.append(f"Wind speed: {wind} {unit_wind}.")
        if wmo:
            parts.append(f"Conditions: {wmo}.")
        return " ".join(parts)


def _wmo_label(code: int | None) -> str:
    if code is None:
        return ""
    # WMO Weather interpretation codes (Open-Meteo)
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
