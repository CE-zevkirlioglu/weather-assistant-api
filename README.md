# Weather Assistant

Personalized weather assistant that aggregates historical Kaggle datasets with live WeatherAPI data to produce actionable recommendations (hot, cold, rainy, windy, high UV, pleasant) for mobile clients via a RESTful service.

## Overview
- **Model**: Multi-output RandomForest (macro F1 ≈ 0.99) trained on unified Kaggle datasets.
- **Live data**: WeatherAPI current conditions endpoint for real-time weather data.
- **Output**: Structured JSON containing feature snapshot, per-label probabilities/confidence, and six recommendation flags.
- **Tech stack**: Python, pandas, scikit-learn, Flask, Flask-CORS.
- **API**: RESTful API with CORS support for mobile applications.
- **Deployment**: Ready for Render.com, Heroku, and other cloud platforms.

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
│   └── server.py               # Flask API service with CORS support
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render.com deployment configuration
├── Procfile                    # Alternative deployment config
├── runtime.txt                 # Python version specification
├── start_backend.bat           # Windows batch script to start backend
├── test_api.py                 # Python test script for API endpoints
├── test.html                   # Browser-based test interface (recommended)
├── .gitignore                  # Git ignore rules
├── run.txt                     # Turkish runbook (detailed setup guide)
├── README.md                   # This file
├── KULLANIM_REHBERI.md        # Complete usage guide (kurulum, test, deploy)
├── DEPLOY.md                   # Render.com deployment guide (detailed)
├── API_DOCS.md                 # Complete API documentation
└── SISTEM_AKISI.md            # System flow explanation (Turkish)
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

### Prerequisites
- Python 3.11+ (see `runtime.txt`)
- WeatherAPI.com API key ([Get one here](https://www.weatherapi.com/))

### Installation
```powershell
# 1. Clone and enter
git clone <repo-url>
cd weather-assistant

# 2. Create and activate virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
$Env:WEATHER_API_KEY = "<your_weatherapi_key>"
$Env:PYTHONPATH = "$PWD\src"
```

### Optional: Regenerate Model
```powershell
# Build training dataset from Kaggle files
python src/build_dataset.py

# Train the model
python src/train.py --csv data/processed/weather_training.csv --out models
```

## Run the API

### Method 1: Direct Python (Recommended)
```powershell
$env:PYTHONPATH="src"
python src/server.py
```

### Method 2: Flask CLI
```powershell
python -m flask --app src.server run --host 0.0.0.0 --port 8000
```

### Method 3: Batch Script (Windows)
```powershell
.\start_backend.bat
```

**Expected output:**
```
 * Running on http://0.0.0.0:8000
 * Running on http://127.0.0.1:8000
```

**Health check:** `http://localhost:8000/health → {"status":"ok","model_loaded":true}`

## Testing the API

### Method 1: Browser Test Interface (Easiest)
1. Start the backend (see "Run the API" above)
2. Open `test.html` in your browser
3. Enter coordinates and click "Hava Durumu Tahmini Al"

### Method 2: Python Test Script
```powershell
# Run comprehensive test suite
python test_api.py
```

### Method 3: Python Test Script
```powershell
python test_api.py
```

### Method 4: Manual Testing

**Health Check:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Predict with Coordinates:**
```powershell
$body = '{"lat":41.0082,"lon":28.9784}'
Invoke-WebRequest -Uri http://localhost:8000/predict `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body $body `
  -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Predict with Manual Features:**
```powershell
curl.exe -X POST "http://localhost:8000/predict" `
  -H "Content-Type: application/json" `
  -d '{"features":{"temp":35,"humidity":40,"wind_speed":12,"pressure":1008,"clouds":20,"uv_index":9}}'
```

**For detailed usage guide, see:**
- `KULLANIM_REHBERI.md` - Complete usage guide (kurulum, çalıştırma, test, deploy)
- `API_DOCS.md` - Complete API documentation

**Sample Response:**
```json
{
  "success": true,
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

## API Endpoints

### `GET /health`
Health check endpoint. Returns API status and model loading state.

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true
}
```

### `POST /predict`
Main prediction endpoint. Accepts coordinates or manual features.

**Request Options:**

1. **Coordinates** (Recommended - uses WeatherAPI for real-time data)
   ```json
   {
     "lat": 41.0082,
     "lon": 28.9784
   }
   ```

2. **Manual Features**
   ```json
   {
     "features": {
       "temp": 35,
       "humidity": 40,
       "wind_speed": 12,
       "pressure": 1008,
       "clouds": 20,
       "uv_index": 9
     }
   }
   ```

**Response Structure:**
- `success`: Boolean indicating request success
- `summary`: Main recommendation message in Turkish
- `recommendations`: Array of all recommendations with active flags
- `features`: Weather data used for prediction
- `prediction`: Model predictions (states, probabilities, confidences)
- `meta`: Location and source information

**For complete API documentation, see `API_DOCS.md`**

## Testing & Tooling

### Available Test Tools
- **`test.html`** - Browser-based visual test interface (recommended)
- **`test_api.py`** - Comprehensive Python test suite
- **`start_backend.bat`** - Windows batch script to start backend easily

### Documentation Files
- **`KULLANIM_REHBERI.md`** - Complete usage guide (kurulum, çalıştırma, test, deploy)
- **`API_DOCS.md`** - Complete API documentation with mobile app examples
- **`SISTEM_AKISI.md`** - System flow explanation in Turkish
- **`DEPLOY.md`** - Render.com deployment guide (detailed)
- **`run.txt`** - Turkish runbook with troubleshooting tips

### Model Metrics
Model performance (printed during `train.py`):
- Rain F1 ≈ 0.94 (precision 0.96, recall 0.91)
- Other labels F1 ≈ 1.00
- Macro F1 ≈ 0.99

## Deployment

### Render.com (Recommended)
- Quick guide: See `KULLANIM_REHBERI.md` → "Render.com'a Deploy" section
- Detailed guide: See `DEPLOY.md` for step-by-step deployment guide

**Quick Deploy:**
1. Push code to GitHub
2. Create new Web Service on Render.com
3. Connect GitHub repository
4. Set environment variables:
   - `WEATHER_API_KEY`: Your WeatherAPI.com key
   - `PYTHONPATH`: `src`
5. Deploy!

**Configuration files:**
- `render.yaml` - Render.com service configuration
- `Procfile` - Alternative deployment config
- `runtime.txt` - Python version specification

### Other Platforms
- **Heroku**: Use `Procfile` with command: `gunicorn --chdir src server:app`
- **Docker**: Create Dockerfile using `requirements.txt`
- **VPS**: Use `gunicorn` with systemd service

### Environment Variables
- **`WEATHER_API_KEY`** (Required): Your WeatherAPI.com API key
- **`PYTHONPATH`** (Required): Set to `src` for module imports
- **`PORT`** (Optional): Server port (default: 8000)

### Important Notes
- Ensure `models/weather_model.pkl` is included in deployment
- CORS is enabled for mobile applications
- Model loads at startup (may take a few seconds)
- WeatherAPI.com has rate limits (check your plan)

## Mobile App Integration

The API is ready for mobile applications! See `API_DOCS.md` for complete integration examples.

**Quick Integration:**
```javascript
// Example: React Native / JavaScript
const response = await fetch('https://your-api.onrender.com/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lat: userLatitude,
    lon: userLongitude
  })
});

const data = await response.json();
console.log(data.summary); // Turkish recommendation message
```

**Features:**
- ✅ CORS enabled for cross-origin requests
- ✅ Real-time weather data from WeatherAPI.com
- ✅ ML-powered predictions and recommendations
- ✅ Structured JSON responses
- ✅ Error handling and validation

## How It Works

1. **Mobile app** sends coordinates (lat, lon) to `/predict` endpoint
2. **Backend** fetches real-time weather data from WeatherAPI.com
3. **ML Model** analyzes weather features and makes predictions
4. **Recommendations** are generated based on model outputs
5. **Response** is returned to mobile app with summary and recommendations

See `SISTEM_AKISI.md` for detailed system flow explanation.

## Support & Extensions

### Future Enhancements
- Extend datasets by adding UV/pressure estimations to additional CSVs
- Introduce calibration or adjust thresholds per region
- Add localization support for recommendation messages (currently Turkish)
- Integrate feedback loop for continuous model updates
- Add caching for frequently requested locations
- Implement rate limiting for API protection

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available for educational purposes.

## Acknowledgments
- WeatherAPI.com for real-time weather data
- Kaggle datasets for model training
- Flask and scikit-learn communities
