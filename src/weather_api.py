def from_current_json(data):
    if not data:
        return {
            "temp": None,
            "humidity": None,
            "wind_speed": None,
            "pressure": None,
            "clouds": None,
            "uv_index": None,
            "condition_text": None,
        }

    # Weather API (weatherapi.com) structure
    if "temp_c" in data or "wind_kph" in data:
        wind_kph = data.get("wind_kph")
        wind_speed = wind_kph * 1000.0 / 3600.0 if wind_kph is not None else None
        condition = data.get("condition") or {}
        return {
            "temp": data.get("temp_c"),
            "humidity": data.get("humidity"),
            "wind_speed": wind_speed,
            "pressure": data.get("pressure_mb"),
            "clouds": data.get("cloud"),
            "uv_index": data.get("uv"),
            "condition_text": condition.get("text"),
        }

    # Legacy OpenWeather structure fallback
    if "main" in data:
        main = data.get("main", {})
        wind = data.get("wind", {})
        clouds = data.get("clouds", {})
        uv = data.get("uvi")
        return {
            "temp": main.get("temp"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "pressure": main.get("pressure"),
            "clouds": clouds.get("all"),
            "uv_index": uv,
            "condition_text": None,
        }

    return {
        "temp": data.get("temp"),
        "humidity": data.get("humidity"),
        "wind_speed": data.get("wind_speed"),
        "pressure": data.get("pressure"),
        "clouds": data.get("clouds"),
        "uv_index": data.get("uv_index") or data.get("uvi"),
        "condition_text": data.get("condition_text"),
    }
