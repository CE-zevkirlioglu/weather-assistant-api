# Sistem Akışı ve Nasıl Çalışıyor?

## 🔄 Tam Akış Şeması

```
test.html (Tarayıcı)
    ↓
    [Kullanıcı koordinat girer: lat=41.0082, lon=28.9784]
    ↓
    [POST /predict isteği gönderilir]
    ↓
Backend (server.py)
    ↓
    [fetch_weatherapi(lat, lon) çağrılır]
    ↓
WeatherAPI.com (Gerçek Hava Durumu Servisi)
    ↓
    [API'den gerçek zamanlı veriler alınır]
    ↓
    {
        "temp": 17.3,
        "humidity": 88.0,
        "wind_speed": 1.61,
        "pressure": 1019.0,
        "clouds": 0.0,
        "uv_index": 0.0
    }
    ↓
Eğitilmiş Model (weather_model.pkl)
    ↓
    [predict_conditions() ile tahmin yapılır]
    ↓
    {
        "label_rain": false,
        "label_hot": false,
        "label_cold": false,
        ...
    }
    ↓
Öneriler Oluşturulur (build_recommendations)
    ↓
    ["Hava durumu oldukca guzel, tadini cikar."]
    ↓
Response JSON
    ↓
test.html (Tarayıcıda gösterilir)
```

---

## 📝 Adım Adım Detaylı Açıklama

### 1️⃣ **test.html'den İstek Gönderilir**

Kullanıcı tarayıcıda koordinatları girer ve "Hava Durumu Tahmini Al" butonuna tıklar:

```javascript
// test.html içinde
const response = await fetch('http://localhost:8000/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        lat: 41.0082,  // İstanbul latitude
        lon: 28.9784   // İstanbul longitude
    })
});
```

---

### 2️⃣ **Backend İsteği Alır**

`server.py` dosyasındaki `/predict` endpoint'i isteği alır:

```python
@app.route("/predict", methods=["POST"])
def predict_endpoint():
    payload = request.get_json()  # {"lat": 41.0082, "lon": 28.9784}
    
    if "lat" in payload and "lon" in payload:
        lat = float(payload["lat"])
        lon = float(payload["lon"])
        
        # WeatherAPI'den gerçek verileri çek
        features, context = fetch_weatherapi(lat, lon)
```

---

### 3️⃣ **WeatherAPI.com'dan Gerçek Veriler Çekilir**

`fetch_weatherapi()` fonksiyonu WeatherAPI.com'a istek gönderir:

```python
def fetch_weatherapi(lat: float, lon: float):
    params = {
        "key": get_api_key(),  # WEATHER_API_KEY environment variable
        "q": f"{lat},{lon}",   # "41.0082,28.9784"
        "aqi": "no",
    }
    
    # WeatherAPI.com'a HTTP GET isteği
    payload = _call_weatherapi(CURRENT_URL, params)
    # CURRENT_URL = "https://api.weatherapi.com/v1/current.json"
```

**WeatherAPI.com'dan dönen gerçek veriler:**
```json
{
    "location": {
        "name": "Istanbul",
        "country": "Turkey",
        "localtime": "2025-01-15 14:30"
    },
    "current": {
        "temp_c": 17.3,
        "humidity": 88,
        "wind_kph": 5.8,
        "pressure_mb": 1019,
        "cloud": 0,
        "uv": 0,
        "condition": {"text": "Clear"}
    }
}
```

Bu veriler parse edilir ve model için hazır hale getirilir:
```python
features = {
    "temp": 17.3,
    "humidity": 88.0,
    "wind_speed": 1.61,  # km/h'den m/s'ye çevrildi
    "pressure": 1019.0,
    "clouds": 0.0,
    "uv_index": 0.0
}
```

---

### 4️⃣ **Eğitilmiş Model ile Tahmin Yapılır**

`predict_conditions()` fonksiyonu eğitilmiş modeli kullanır:

```python
# predict.py içinde
def predict_conditions(features: Dict[str, float], model_bundle=None):
    bundle = model_bundle or load_model()  # models/weather_model.pkl yüklenir
    estimator = bundle["model"]  # Eğitilmiş RandomForest modeli
    
    # Features'ları DataFrame'e çevir
    x = _prepare_row(features, feature_columns)
    
    # Model tahmin yapar
    preds = estimator.predict(x)[0]
    
    # Olasılıklar hesaplanır
    probas = estimator.predict_proba(x)
    
    return {
        "states": {
            "label_rain": False,
            "label_hot": False,
            "label_cold": False,
            "label_uv_high": False,
            "label_windy": False
        },
        "probabilities": {
            "label_rain": 0.0614,
            "label_hot": 0.0401,
            ...
        },
        "label": "NoRain"
    }
```

**Model ne yapıyor?**
- Eğitildiği Kaggle veri setlerindeki pattern'leri kullanarak
- Gerçek zamanlı hava durumu verilerini analiz ediyor
- Yağmur, sıcaklık, UV, rüzgar gibi durumları tahmin ediyor

---

### 5️⃣ **Öneriler Oluşturulur**

`build_recommendations()` fonksiyonu model çıktılarına göre öneriler oluşturur:

```python
def build_recommendations(prediction: Dict):
    states = prediction.get("states", {})
    
    flags = {
        "hot": bool(states.get("label_hot")),      # True/False
        "cold": bool(states.get("label_cold")),    # True/False
        "uv_high": bool(states.get("label_uv_high")), # True/False
        "windy": bool(states.get("label_windy")),  # True/False
        "rain": bool(states.get("label_rain")),    # True/False
    }
    
    # Öneriler oluşturulur
    recommendations = [
        {"id": "hot", "message": "Hava cok sicak, ince giyin.", "active": False},
        {"id": "cold", "message": "Hava cok soguk, kalin giyin.", "active": False},
        {"id": "rain", "message": "Hava yagmurlu, semsiye almayi unutmayin.", "active": False},
        {"id": "pleasant", "message": "Hava durumu oldukca guzel, tadini cikar.", "active": True}
    ]
    
    return summary, recommendations
```

---

### 6️⃣ **Response Döndürülür**

Backend JSON response döndürür:

```json
{
    "success": true,
    "features": {
        "temp": 17.3,
        "humidity": 88.0,
        "wind_speed": 1.61,
        "pressure": 1019.0,
        "clouds": 0.0,
        "uv_index": 0.0
    },
    "prediction": {
        "states": {...},
        "probabilities": {...},
        "label": "NoRain"
    },
    "summary": "Hava durumu oldukca guzel, tadini cikar.",
    "recommendations": [...],
    "meta": {
        "source": "weatherapi",
        "location_name": "Istanbul",
        "location_country": "Turkey",
        "local_time": "2025-01-15 14:30"
    }
}
```

---

### 7️⃣ **test.html Sonuçları Gösterir**

Tarayıcıda sonuçlar gösterilir:
- ✅ Özet mesaj
- 📍 Konum bilgisi
- 💡 Aktif öneriler
- 📊 Hava durumu verileri

---

## 🎯 Özet

**Evet, tam olarak şöyle çalışıyor:**

1. ✅ **test.html** → Koordinatları gönderir
2. ✅ **Backend** → WeatherAPI.com'dan **gerçek zamanlı** hava durumu verilerini alır
3. ✅ **Model** → Bu gerçek verileri analiz eder ve tahmin yapar
4. ✅ **Öneriler** → Model çıktılarına göre öneriler oluşturulur
5. ✅ **Response** → Sonuçlar test.html'de gösterilir

**Önemli Noktalar:**
- 🌐 WeatherAPI.com **gerçek zamanlı** hava durumu servisi kullanılıyor
- 🤖 Eğitilmiş **machine learning modeli** tahmin yapıyor
- 📱 Mobil uygulama da aynı şekilde çalışacak
- 🔄 Her istekte **güncel** hava durumu verileri alınıyor

---

## 🔍 Doğrulama

Backend loglarında görebilirsiniz:
- WeatherAPI.com'a istek gönderildiğinde
- Model tahmin yaptığında
- Response döndürüldüğünde

Test ederken backend penceresini açık tutun, logları görebilirsiniz!

