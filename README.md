# Weather Assistant

Personalized weather assistant that aggregates historical Kaggle datasets with live WeatherAPI data to produce actionable recommendations (hot, cold, rainy, windy, high UV, pleasant) for mobile clients via a RESTful service.

## Overview
- **Model**: Multi-output RandomForest (macro F1 ≈ 0.99) trained on unified Kaggle datasets.
- **Live data**: WeatherAPI current conditions endpoint.
- **Output**: Structured JSON containing feature snapshot, per-label probabilities/confidence, and six recommendation flags.
- **Tech stack**: Python, pandas, scikit-learn, Flask.

## Project Structure
```
weather-assistant/
├── app/
│   └── demo_gradio.py          # legacy demo (not required)
├── data/
│   ├── kaggle/                 # raw Kaggle CSVs
│   └── processed/
│       └── weather_training.csv
├── models/
│   └── weather_model.pkl       # trained multi-label model bundle
├── src/
│   ├── build_dataset.py        # merges Kaggle datasets, builds labels
│   ├── prepare_data.py         # training loader helpers
│   ├── train.py                # model training entrypoint
│   ├── predict.py              # inference & recommendation helpers
│   ├── weather_api.py          # WeatherAPI normalization utilities
│   └── server.py               # Flask API service
├── requirements.txt            # optional; core packages installed manually
├── run.txt                     # Turkish runbook (detailed setup guide)
└── README.md
```

## Datasets
Place Kaggle files under `data/kaggle/`:
- `weather_forecast_data.csv`
- `weather_classification_data.csv`
- `GlobalWeatherRepository.csv`
- `weatherHistory.csv`

`build_dataset.py` normalizes features (temp, humidity, wind, pressure, clouds, uv_index) and derives labels:
- `label_rain`, `label_hot`, `label_cold`, `label_uv_high`, `label_windy`

## Quick Start
```powershell
# 1. clone and enter
git clone <repo-url>
cd weather-assistant

# 2. create + activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. install core dependencies
pip install pandas numpy scikit-learn joblib requests python-dateutil flask

# 4. environment variables (current session)
$Env:WEATHER_API_KEY = "<your_weatherapi_key>"
$Env:PYTHONPATH = "$PWD\src"
```
Optional regeneration:
```powershell
python src/build_dataset.py
python src/train.py --csv data/processed/weather_training.csv --out models
```

## Run the API
```powershell
python -m flask --app src.server run --host 0.0.0.0 --port 8000
# or
python -c "import sys; sys.path.append('src'); import server; server.run()"
```
Health check: `http://localhost:8000/health → {"status":"ok"}`

## Testing the Endpoint
Open a new terminal (activate the virtual env if needed) and use one of the following:

### cURL (coordinates)
```powershell
curl.exe -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d '{"lat":41.0082,"lon":28.9784}'
```

### cURL (manual features)
```powershell
curl.exe -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d '{"features":{"temp":35,"humidity":40,"wind_speed":12,"pressure":1008,"clouds":20,"uv_index":9}}'
```

### PowerShell `Invoke-WebRequest`
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/predict" `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"lat":41.0082,"lon":28.9784}'

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

Sample response:
```json
{
  "features": {
    "clouds": 0.0,
    "humidity": 88.0,
    "pressure": 1019.0,
    "temp": 17.3,
    "uv_index": 0.0,
    "wind_speed": 1.61
  },
  "meta": {
    "condition": "Clear",
    "lat": 41.0082,
    "local_time": "2025-11-08 20:31",
    "location_country": "Turkey",
    "location_name": "Istanbul",
    "location_region": "Istanbul",
    "lon": 28.9784,
    "source": "weatherapi"
  },
  "prediction": {
    "confidences": {
      "label_cold": "high",
      "label_hot": "high",
      "label_rain": "high",
      "label_uv_high": "high",
      "label_windy": "high"
    },
    "label": "NoRain",
    "proba": 0.0614,
    "probabilities": {
      "label_cold": 0.0026,
      "label_hot": 0.0401,
      "label_rain": 0.0614,
      "label_uv_high": 0.0,
      "label_windy": 0.0519
    },
    "states": {
      "label_cold": false,
      "label_hot": false,
      "label_rain": false,
      "label_uv_high": false,
      "label_windy": false
    }
  },
  "recommendations": [
    {"id": "hot", "message": "Hava cok sicak, ince giyin.", "active": false},
    {"id": "cold", "message": "Hava cok soguk, kalin giyin.", "active": false},
    {"id": "uv_high", "message": "UV cok fazla, gunes kremi surun.", "active": false},
    {"id": "windy", "message": "Hava cok ruzgarli, kapsonlu giyin.", "active": false},
    {"id": "rain", "message": "Hava yagmurlu, semsiye almayi unutmayin.", "active": false},
    {"id": "pleasant", "message": "Hava durumu oldukca guzel, tadini cikar.", "active": true}
  ],
  "summary": "Hava durumu oldukca guzel, tadini cikar."
}
```

## API Usage
### `POST /predict`
Request options:
- **Coordinates** (WeatherAPI lookup)
  ```json
  { "lat": 41.0082, "lon": 28.9784 }
  ```
- **Manual features**
  ```json
  { "features": { "temp": 35, "humidity": 40, "wind_speed": 12, "pressure": 1008, "clouds": 20, "uv_index": 9 } }
  ```

Sample response:
```json
{
  "summary": "Hava durumu oldukca guzel, tadini cikar.",
  "recommendations": [
    {"id": "hot", "message": "Hava cok sicak, ince giyin.", "active": false},
    {"id": "pleasant", "message": "Hava durumu oldukca guzel, tadini cikar.", "active": true}
  ],
  "prediction": {
    "states": {"label_rain": false, "label_hot": false, ...},
    "probabilities": {"label_rain": 0.06, ...},
    "confidences": {"label_rain": "high", ...},
    "label": "NoRain",
    "proba": 0.06
  },
  "features": {"temp": 17.3, "humidity": 88.0, ...},
  "meta": {"location_name": "Istanbul", "source": "weatherapi", ...}
}
```

## Testing & Tooling
- `run.txt` contains a Turkish step-by-step runbook with troubleshooting tips.
- Use `Invoke-WebRequest` or `curl.exe` to validate responses while Flask server runs in a separate PowerShell window.
- Model metrics (printed during `train.py`):
  - Rain F1 ≈ 0.94 (precision 0.96, recall 0.91)
  - Other labels F1 ≈ 1.00
  - Macro F1 ≈ 0.99

## Deployment Notes
- Required environment variables: `WEATHER_API_KEY`, `PYTHONPATH=src` (or adjust module path).
- Boot command for platforms like Render/Heroku: `gunicorn server:app --chdir src`
- Ensure `models/weather_model.pkl` is bundled or accessible.
- **Render.com Deployment**: Detaylı deploy rehberi için `DEPLOY.md` dosyasına bakın.
- **CORS**: Mobil uygulamalar için CORS desteği aktif durumda.

## Support & Extensions
- Extend datasets by adding UV/pressure estimations to additional CSVs.
- Introduce calibration or adjust thresholds per region.
- Add localization support for recommendation messages.
- Integrate feedback loop for continuous model updates.
