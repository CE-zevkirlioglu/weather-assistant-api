import os
from typing import Dict, Optional, Tuple

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from weather_api import from_current_json
from predict import load_model, predict_conditions


REQUIRED_FEATURES = ["temp", "humidity", "wind_speed", "pressure", "clouds"]
DEFAULT_API_KEY = "daec79c46ef54c2593693338250811"
CURRENT_URL = "https://api.weatherapi.com/v1/current.json"


def get_api_key() -> str:
    return os.getenv("WEATHER_API_KEY", DEFAULT_API_KEY)


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


def build_recommendations(prediction: Dict, features: Optional[Dict[str, float]] = None) -> Tuple[str, list]:
    states = prediction.get("states", {})

    flags = {
        "hot": bool(states.get("label_hot")),
        "cold": bool(states.get("label_cold")),
        "uv_high": bool(states.get("label_uv_high")),
        "windy": bool(states.get("label_windy")),
        "rain": bool(states.get("label_rain")),
    }

    # Ek kontrol: Model 10°C'nin altını "cold" olarak işaretliyor ama
    # 10-15°C arası da çoğu insan için soğuk sayılır. Bu aralığı da kontrol edelim.
    if features and "temp" in features:
        temp = features["temp"]
        # 15°C ve altı soğuk kabul edilir (model eşiği 10°C ama gerçekçi eşik 15°C)
        if temp <= 15.0 and not flags["cold"]:
            flags["cold"] = True

    # Ek kontrol: UV indeksi için de gerçekçi eşik kontrolü
    if features and "uv_index" in features:
        uv_index = features["uv_index"]
        # 5 ve üzeri UV yüksek kabul edilir (model eşiği 7 ama gerçekçi eşik 5)
        if uv_index >= 5.0 and not flags["uv_high"]:
            flags["uv_high"] = True

    pleasant_active = not any(flags.values())

    templates = [
        ("hot", "Hava çok sıcak! Hafif ve nefes alabilen kıyafetler tercih edin, bol su tüketmeyi unutmayın."),
        ("cold", "Hava oldukça soğuk. Kalın giysiler giyin ve vücut sıcaklığınızı korumaya dikkat edin."),
        ("uv_high", "UV indeksi yüksek! Güneş kremi kullanmayı ve şapka takmayı unutmayın. Öğle saatlerinde güneşten kaçının."),
        ("windy", "Rüzgar oldukça kuvvetli. Kapşonlu veya rüzgar geçirmeyen kıyafetler tercih edin."),
        ("rain", "Yağmur bekleniyor! Yanınıza şemsiye almayı ve su geçirmez kıyafetler giymeyi unutmayın."),
        ("pleasant", "Hava durumu harika! Dışarıda vakit geçirmek için mükemmel bir gün. Keyfini çıkarın!"),
    ]

    recommendations = []
    for rec_id, message in templates:
        if rec_id == "pleasant":
            active = pleasant_active
        else:
            active = flags.get(rec_id, False)
        recommendations.append({"id": rec_id, "message": message, "active": active})

    summary = next((rec["message"] for rec in recommendations if rec["active"]), templates[-1][1])
    return summary, recommendations


app = Flask(__name__)
# CORS desteği - mobil uygulama için tüm origin'lere izin ver
CORS(app, resources={r"/*": {"origins": "*"}})

# Model'i başlangıçta yükle
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
    # OPTIONS isteği için CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    if MODEL is None:
        return jsonify({"error": "Model not loaded. Please check server logs."}), 500
    
    payload = request.get_json(force=True, silent=True) or {}

    # Konum bilgisi kontrolü
    if not payload:
        return jsonify({"error": "Request body is required"}), 400

    features = None
    meta: Dict[str, Optional[float]] = {}
    try:
        if "lat" in payload and "lon" in payload:
            lat = float(payload["lat"])
            lon = float(payload["lon"])
            
            # Koordinat validasyonu
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
        prediction = predict_conditions(features, model_bundle=MODEL)
        summary, recommendations = build_recommendations(prediction, features)
        response = {
            "success": True,
            "features": features,
            "prediction": prediction,
            "summary": summary,
            "recommendations": recommendations,
            "meta": meta,
        }
        return jsonify(response)
    except Exception as exc:
        return jsonify({"error": "Prediction failed", "detail": str(exc)}), 500


def run() -> None:
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=False)


if __name__ == "__main__":
    run()

