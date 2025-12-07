# Weather Assistant API Dokümantasyonu

Bu dokümantasyon, mobil uygulama entegrasyonu için Weather Assistant API'sinin kullanımını açıklar.

## Base URL

**Local Development:**
```
http://localhost:8000
```

**Production (Render.com):**
```
https://weather-assistant-api.onrender.com
```

## Endpoints

### 1. Health Check

API'nin çalışıp çalışmadığını ve modelin yüklü olup olmadığını kontrol eder.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true
}
```

**Status Codes:**
- `200`: Başarılı

---

### 2. Weather Prediction (Mobil Uygulama İçin)

Kullanıcının konumuna göre hava durumu tahmini ve öneriler döndürür.

**Endpoint:** `POST /predict`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body (Konum ile - Önerilen):**
```json
{
  "lat": 41.0082,
  "lon": 28.9784
}
```

**Request Body (Manuel Feature'lar ile):**
```json
{
  "features": {
    "temp": 25,
    "humidity": 60,
    "wind_speed": 5,
    "pressure": 1013,
    "clouds": 30,
    "uv_index": 6
  }
}
```

**Response (Başarılı):**
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
    "states": {
      "label_rain": false,
      "label_hot": false,
      "label_cold": false,
      "label_uv_high": false,
      "label_windy": false
    },
    "probabilities": {
      "label_rain": 0.0614,
      "label_hot": 0.0401,
      "label_cold": 0.0026,
      "label_uv_high": 0.0,
      "label_windy": 0.0519
    },
    "confidences": {
      "label_rain": "high",
      "label_hot": "high",
      "label_cold": "high",
      "label_uv_high": "high",
      "label_windy": "high"
    },
    "label": "NoRain",
    "proba": 0.0614
  },
  "summary": "Hava durumu oldukca guzel, tadini cikar.",
  "recommendations": [
    {
      "id": "hot",
      "message": "Hava cok sicak, ince giyin.",
      "active": false
    },
    {
      "id": "cold",
      "message": "Hava cok soguk, kalin giyin.",
      "active": false
    },
    {
      "id": "uv_high",
      "message": "UV cok fazla, gunes kremi surun.",
      "active": false
    },
    {
      "id": "windy",
      "message": "Hava cok ruzgarli, kapsonlu giyin.",
      "active": false
    },
    {
      "id": "rain",
      "message": "Hava yagmurlu, semsiye almayi unutmayin.",
      "active": false
    },
    {
      "id": "pleasant",
      "message": "Hava durumu oldukca guzel, tadini cikar.",
      "active": true
    }
  ],
  "meta": {
    "source": "weatherapi",
    "lat": 41.0082,
    "lon": 28.9784,
    "location_name": "Istanbul",
    "location_region": "Istanbul",
    "location_country": "Turkey",
    "local_time": "2025-11-08 20:31",
    "condition": "Clear"
  }
}
```

**Response (Hata):**
```json
{
  "error": "Invalid coordinates. lat must be between -90 and 90, lon must be between -180 and 180"
}
```

**Status Codes:**
- `200`: Başarılı
- `400`: Geçersiz istek (eksik parametreler, geçersiz koordinatlar)
- `403`: WeatherAPI yetkilendirme hatası
- `500`: Sunucu hatası (model yüklenemedi, tahmin hatası)
- `502`: WeatherAPI servisine erişilemedi

---

## Mobil Uygulama Entegrasyonu Örnekleri

### React Native / JavaScript

```javascript
const API_BASE_URL = 'https://weather-assistant-api.onrender.com';

async function getWeatherPrediction(latitude, longitude) {
  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        lat: latitude,
        lon: longitude
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'API request failed');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Weather prediction error:', error);
    throw error;
  }
}

// Kullanım
const userLocation = { lat: 41.0082, lon: 28.9784 };
const result = await getWeatherPrediction(userLocation.lat, userLocation.lon);

console.log(result.summary); // "Hava durumu oldukca guzel, tadini cikar."
console.log(result.recommendations.filter(r => r.active)); // Aktif öneriler
```

### Swift (iOS)

```swift
import Foundation

struct WeatherResponse: Codable {
    let success: Bool
    let summary: String
    let recommendations: [Recommendation]
    let features: [String: Double]
    let meta: Meta
}

struct Recommendation: Codable {
    let id: String
    let message: String
    let active: Bool
}

struct Meta: Codable {
    let location_name: String?
    let location_country: String?
    let lat: Double?
    let lon: Double?
}

func getWeatherPrediction(lat: Double, lon: Double) async throws -> WeatherResponse {
    let url = URL(string: "https://weather-assistant-api.onrender.com/predict")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body: [String: Double] = ["lat": lat, "lon": lon]
    request.httpBody = try JSONSerialization.data(withJSONObject: body)
    
    let (data, response) = try await URLSession.shared.data(for: request)
    
    guard let httpResponse = response as? HTTPURLResponse,
          httpResponse.statusCode == 200 else {
        throw URLError(.badServerResponse)
    }
    
    return try JSONDecoder().decode(WeatherResponse.self, from: data)
}

// Kullanım
Task {
    do {
        let result = try await getWeatherPrediction(lat: 41.0082, lon: 28.9784)
        print(result.summary)
        let activeRecommendations = result.recommendations.filter { $0.active }
        print(activeRecommendations)
    } catch {
        print("Error: \(error)")
    }
}
```

### Kotlin (Android)

```kotlin
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

data class WeatherResponse(
    val success: Boolean,
    val summary: String,
    val recommendations: List<Recommendation>,
    val features: Map<String, Double>,
    val meta: Meta
)

data class Recommendation(
    val id: String,
    val message: String,
    val active: Boolean
)

data class Meta(
    val location_name: String?,
    val location_country: String?,
    val lat: Double?,
    val lon: Double?
)

suspend fun getWeatherPrediction(lat: Double, lon: Double): WeatherResponse {
    val client = OkHttpClient()
    val mediaType = "application/json".toMediaType()
    
    val jsonBody = JSONObject()
        .put("lat", lat)
        .put("lon", lon)
    
    val requestBody = jsonBody.toString().toRequestBody(mediaType)
    
    val request = Request.Builder()
        .url("https://weather-assistant-api.onrender.com/predict")
        .post(requestBody)
        .addHeader("Content-Type", "application/json")
        .build()
    
    val response = client.newCall(request).execute()
    val responseBody = response.body?.string() ?: throw Exception("Empty response")
    
    // JSON parsing (Gson veya Moshi kullanabilirsiniz)
    // Burada basit bir örnek gösteriliyor
    return parseWeatherResponse(responseBody)
}
```

---

## Response Alanları Açıklaması

### `summary`
Kısa özet mesaj. Aktif olan ilk önerinin mesajı veya "pleasant" mesajı.

### `recommendations`
Tüm önerilerin listesi. Her öneri:
- `id`: Öneri kimliği (hot, cold, uv_high, windy, rain, pleasant)
- `message`: Türkçe öneri mesajı
- `active`: Bu önerinin aktif olup olmadığı (boolean)

### `prediction.states`
Model tahminlerinin boolean değerleri:
- `label_rain`: Yağmur bekleniyor mu?
- `label_hot`: Hava çok sıcak mı?
- `label_cold`: Hava çok soğuk mu?
- `label_uv_high`: UV indeksi yüksek mi?
- `label_windy`: Hava rüzgarlı mı?

### `prediction.probabilities`
Her label için olasılık değerleri (0.0 - 1.0 arası).

### `prediction.confidences`
Her label için güven seviyesi:
- `high`: Yüksek güven (>0.8 veya <0.2)
- `medium`: Orta güven (0.4-0.6 arası)
- `low`: Düşük güven

### `meta`
Ek bilgiler:
- `source`: Veri kaynağı ("weatherapi" veya "payload.features")
- `lat`, `lon`: Kullanılan koordinatlar
- `location_name`: Şehir adı
- `location_country`: Ülke adı
- `local_time`: Yerel saat
- `condition`: Hava durumu açıklaması

---

## Hata Yönetimi

API hata durumlarında şu formatı kullanır:

```json
{
  "error": "Hata mesajı",
  "detail": "Detaylı hata bilgisi (opsiyonel)"
}
```

**Önerilen Hata Yönetimi:**
1. Network hatalarını yakalayın (timeout, connection error)
2. HTTP status kodlarını kontrol edin
3. `error` alanını kullanıcıya gösterin
4. Retry mekanizması ekleyin (özellikle Render.com free plan için)

---

## Rate Limiting

Şu anda rate limiting yoktur. Ancak production kullanımında:
- Render.com free plan'da sınırlamalar olabilir
- WeatherAPI.com'un kendi rate limitleri vardır
- Aşırı kullanımda servis geçici olarak kapanabilir

---

## CORS

API CORS desteği ile yapılandırılmıştır. Tüm origin'lerden gelen isteklere izin verilir.

---

## Notlar

- İlk request biraz yavaş olabilir (cold start - Render.com free plan)
- Model dosyası başlangıçta yüklenir, bu yüzden ilk request biraz gecikebilir
- WeatherAPI.com API key'i environment variable olarak ayarlanmalıdır

