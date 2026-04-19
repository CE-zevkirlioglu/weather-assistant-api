import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from weather_api import from_current_json
from predict import load_model, predict_conditions


def _load_project_env_file() -> None:
    """Load KEY=VALUE lines from repo-root .env into os.environ (no extra package required).

    Runs even when python-dotenv is not installed — avoids silently skipping .env on fresh venvs.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    try:
        raw = env_path.read_text(encoding="utf-8-sig")  # utf-8-sig strips Windows BOM
    except OSError:
        return
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        # Prefer existing non-empty shell values; fill from file if unset or blank
        current = os.environ.get(key, "")
        if not current.strip():
            os.environ[key] = value


def _load_dotenv_optional() -> None:
    """Optional richer parsing if python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")


_load_project_env_file()
_load_dotenv_optional()

REQUIRED_FEATURES = ["temp", "humidity", "wind_speed", "pressure", "clouds"]
CURRENT_URL = "https://api.weatherapi.com/v1/current.json"


def get_api_key() -> str:
    key = (os.getenv("WEATHER_API_KEY") or "").strip()
    if not key:
        raise ValueError(
            "WEATHER_API_KEY is not set. Copy .env.example to .env in the project root and add "
            "your key from https://www.weatherapi.com/signup.aspx (free tier available)."
        )
    return key


def _call_weatherapi(url: str, params: Dict[str, str]) -> Dict[str, float]:
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code == 401:
        raise PermissionError("Unauthorized WeatherAPI request.")
    resp.raise_for_status()
    return resp.json()


def fetch_weatherapi(lat: float, lon: float) -> Tuple[Dict[str, float], Dict[str, str]]:
    params = {
        "key": get_api_key(),
        "q": f"{lat},{lon}",
        "aqi": "no",
    }
    payload = _call_weatherapi(CURRENT_URL, params)
    current = payload.get("current") or {}
    location = payload.get("location") or {}
    parsed = from_current_json(current)

    missing = [k for k in REQUIRED_FEATURES if parsed.get(k) is None]
    if missing:
        raise ValueError(f"Missing features from WeatherAPI response: {missing}")

    features: Dict[str, float] = {k: float(parsed[k]) for k in REQUIRED_FEATURES}
    if parsed.get("uv_index") is not None:
        features["uv_index"] = float(parsed["uv_index"])
    else:
        features["uv_index"] = 0.0

    context = {
        "location_name": location.get("name"),
        "location_region": location.get("region"),
        "location_country": location.get("country"),
        "local_time": location.get("localtime"),
        "condition": parsed.get("condition_text"),
    }
    return features, context


FACTOR_LABELS_EN = {
    "rain": "rain",
    "cold": "cold conditions",
    "heat": "high heat",
    "uv": "high UV",
    "wind": "strong wind",
}


def format_factors_en(factors: List[str]) -> str:
    """Join factor codes into readable English, e.g. ['rain','cold'] → 'rain and cold conditions'."""
    labels = [FACTOR_LABELS_EN[f] for f in factors if f in FACTOR_LABELS_EN]
    if not labels:
        return "variable weather conditions"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def build_summary_and_general_message(
    risk_level: str,
    risk_factors: List[str],
    pleasant_active: bool,
) -> Tuple[str, Optional[str]]:
    """Returns (summary text, optional general_risk recommendation message)."""
    if pleasant_active:
        return (
            "Outdoor risk is low. Conditions appear generally favorable.",
            None,
        )

    factor_text = format_factors_en(risk_factors)

    if risk_level == "low":
        summary = f"Outdoor risk is low. Main factors: {factor_text}."
        general_risk = None
    elif risk_level == "moderate":
        summary = f"Outdoor risk is moderate. Main factors: {factor_text}."
        general_risk = "Exercise caution with outdoor plans given the current conditions."
    elif risk_level == "high":
        summary = f"Outdoor risk is high. Main factors: {factor_text}."
        general_risk = "Be cautious outdoors and make any preparations you may need."
    else:
        summary = f"Outdoor risk is very high. Main factors: {factor_text}."
        general_risk = "Consider postponing prolonged outdoor activities if possible."

    return summary, general_risk


def coerce_features(raw: Dict) -> Dict[str, float]:
    features: Dict[str, Optional[float]] = {}
    for key in REQUIRED_FEATURES:
        value = raw.get(key)
        if value is None:
            raise ValueError(f"Missing required feature '{key}' in payload.")
        features[key] = float(value)
    uv_value = raw.get("uv_index")
    features["uv_index"] = float(uv_value) if uv_value is not None else 0.0
    return features  # type: ignore[return-value]


def build_recommendations(
    prediction: Dict,
    features: Optional[Dict[str, float]] = None,
) -> Tuple[str, List[Dict], Dict]:
    states = prediction.get("states", {})
    probabilities = prediction.get("probabilities", {})

    flags = {
        "hot": bool(states.get("label_hot")),
        "cold": bool(states.get("label_cold")),
        "uv_high": bool(states.get("label_uv_high")),
        "windy": bool(states.get("label_windy")),
        "rain": bool(states.get("label_rain")),
    }

    # Post-processing safety checks (see paper: methodology, System Backend section)
    if features and "temp" in features:
        temp = features["temp"]
        if temp <= 15.0 and not flags["cold"]:
            flags["cold"] = True
    if features and "uv_index" in features:
        uv_index = features["uv_index"]
        if uv_index >= 5.0 and not flags["uv_high"]:
            flags["uv_high"] = True

    pleasant_active = not any(flags.values())

    # -----------------------------
    # Risk factors
    # -----------------------------
    risk_factors = []
    if flags["rain"]:
        risk_factors.append("rain")
    if flags["cold"]:
        risk_factors.append("cold")
    if flags["hot"]:
        risk_factors.append("heat")
    if flags["uv_high"]:
        risk_factors.append("uv")
    if flags["windy"]:
        risk_factors.append("wind")

    # -----------------------------
    # Risk component helpers
    # -----------------------------
    def get_probability(label_key: str) -> float:
        value = probabilities.get(label_key, 0.0)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def compute_wind_risk(wind_speed: Optional[float]) -> float:
        if wind_speed is None:
            return 0.0
        # wind_speed: m/s (API). Convert to km/h for thresholds (15, 30, 45 km/h)
        wind_kmh = wind_speed * 3.6
        if wind_kmh < 15:
            return 0.1
        elif wind_kmh < 30:
            return 0.3
        elif wind_kmh < 45:
            return 0.6
        return 0.9

    def compute_uv_risk(uv_index: Optional[float]) -> float:
        if uv_index is None:
            return 0.0
        if uv_index < 3:
            return 0.1
        elif uv_index < 6:
            return 0.3
        elif uv_index < 8:
            return 0.6
        return 0.9

    def compute_temperature_risk(temp: Optional[float]) -> float:
        if temp is None:
            return 0.0
        if 18 <= temp <= 26:
            return 0.1
        elif 10 <= temp < 18:
            return 0.3
        elif 26 < temp <= 32:
            return 0.4
        elif 5 <= temp < 10:
            return 0.6
        elif 32 < temp <= 36:
            return 0.7
        return 0.9

    # -----------------------------
    # Risk score
    # -----------------------------
    rain_probability = get_probability("label_rain")
    wind_speed = features.get("wind_speed") if features else None
    uv_index = features.get("uv_index") if features else None
    temp = features.get("temp") if features else None

    wind_risk = compute_wind_risk(wind_speed)
    uv_risk = compute_uv_risk(uv_index)
    temp_risk = compute_temperature_risk(temp)

    linear_score = (
        0.40 * rain_probability
        + 0.25 * wind_risk
        + 0.20 * uv_risk
        + 0.15 * temp_risk
    )

    active_count = sum(flags.values())
    if active_count >= 3:
        linear_score += 0.10
    elif active_count == 2:
        linear_score += 0.05

    # Hybrid aggregation: the composite index must reflect both compound
    # adversity (weighted sum + bonus) and single-extreme conditions
    # (max of individual severities), so that a single high-severity factor
    # is not diluted by comfortable ones under the weighted sum alone.
    severity_max = max(rain_probability, wind_risk, uv_risk, temp_risk)
    risk_score = min(round(max(linear_score, severity_max), 3), 1.0)

    # Align risk_factors with component scores (add factors even if flags disagree)
    if wind_risk >= 0.6 and "wind" not in risk_factors:
        risk_factors.append("wind")
    if uv_risk >= 0.6 and "uv" not in risk_factors:
        risk_factors.append("uv")
    if temp_risk >= 0.6 and temp is not None:
        if temp < 18 and "cold" not in risk_factors:
            risk_factors.append("cold")
        elif temp > 26 and "heat" not in risk_factors:
            risk_factors.append("heat")

    def compute_risk_level(score: float) -> str:
        if score < 0.25:
            return "low"
        elif score < 0.50:
            return "moderate"
        elif score < 0.75:
            return "high"
        return "very_high"

    risk_level = compute_risk_level(risk_score)

    # Component risks can raise the score even if all model labels are 0.
    # "Favorable" requires no flags and risk_level low.
    if pleasant_active and risk_level != "low":
        pleasant_active = False

    # -----------------------------
    # Recommendation templates
    # -----------------------------
    templates = [
        ("hot", "It's very hot. Wear light, breathable clothing and drink plenty of water."),
        ("cold", "It's quite cold. Dress warmly and protect your core temperature."),
        ("uv_high", "UV index is high. Use sunscreen and a hat; limit midday sun exposure."),
        ("windy", "Wind is strong. Prefer hooded or wind-resistant outer layers."),
        ("rain", "Rain is likely. Bring an umbrella and wear water-resistant clothing."),
        ("pleasant", "Conditions look generally favorable. Good for spending time outside."),
    ]

    recommendations = []
    for rec_id, message in templates:
        if rec_id == "pleasant":
            active = pleasant_active
        else:
            active = flags.get(rec_id, False)
        recommendations.append({"id": rec_id, "message": message, "active": active})

    summary, general_risk_message = build_summary_and_general_message(
        risk_level=risk_level,
        risk_factors=risk_factors,
        pleasant_active=pleasant_active,
    )

    if general_risk_message:
        recommendations.append({
            "id": "general_risk",
            "message": general_risk_message,
            "active": True,
        })

    risk_summary = {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
    }

    return summary, recommendations, risk_summary


app = Flask(__name__)
# CORS: allow all origins (mobile clients)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load model at startup
try:
    MODEL = load_model()
except Exception as e:
    print(f"Warning: Model could not be loaded: {e}")
    MODEL = None


@app.route("/health", methods=["GET"])
def health() -> Dict[str, str]:
    status = {
        "status": "ok",
        "model_loaded": MODEL is not None
    }
    return jsonify(status)


@app.route("/predict", methods=["POST", "OPTIONS"])
def predict_endpoint():
    # CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    if MODEL is None:
        return jsonify({"error": "Model not loaded. Please check server logs."}), 500
    
    payload = request.get_json(force=True, silent=True) or {}

    # Require a JSON body
    if not payload:
        return jsonify({"error": "Request body is required"}), 400

    features = None
    meta: Dict[str, Any] = {}
    try:
        if "lat" in payload and "lon" in payload:
            lat = float(payload["lat"])
            lon = float(payload["lon"])
            
            # Coordinate bounds
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return jsonify({"error": "Invalid coordinates. lat must be between -90 and 90, lon must be between -180 and 180"}), 400
            
            features, context = fetch_weatherapi(lat, lon)
            meta["source"] = "weatherapi"
            meta["lat"] = lat
            meta["lon"] = lon
            meta.update(context)
        elif "features" in payload:
            features = coerce_features(payload["features"])
            meta["source"] = "payload.features"
        else:
            features = coerce_features(payload)
            meta["source"] = "payload.direct"
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except requests.RequestException as exc:
        return jsonify({"error": "Failed to reach WeatherAPI service", "detail": str(exc)}), 502
    except Exception as exc:
        return jsonify({"error": "Internal server error", "detail": str(exc)}), 500

    try:
        explain_requested = request.args.get("explain", "").lower() in ("true", "1", "yes")
        prediction = predict_conditions(
            features, model_bundle=MODEL, include_explanation=explain_requested
        )
        summary, recommendations, risk_summary = build_recommendations(prediction, features)
        response = {
            "success": True,
            "features": features,
            "states": prediction.get("states", {}),
            "probabilities": prediction.get("probabilities", {}),
            "confidences": prediction.get("confidences", {}),
            "label": prediction.get("label", "NoRain"),
            "proba": prediction.get("proba"),
            "summary": summary,
            "risk_summary": risk_summary,
            "recommendations": recommendations,
            "meta": meta,
        }
        if "explanation" in prediction:
            response["explanation"] = prediction["explanation"]
        return jsonify(response)
    except Exception as exc:
        return jsonify({"error": "Prediction failed", "detail": str(exc)}), 500


def run() -> None:
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=False)


if __name__ == "__main__":
    run()
