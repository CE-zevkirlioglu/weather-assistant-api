# Backend Test Rehberi

Bu rehber, Weather Assistant API'sini nasıl başlatıp test edeceğinizi gösterir.

## 1. Backend'i Başlatma

### Yöntem 1: Python ile Direkt Çalıştırma (Önerilen)

**PowerShell'de:**
```powershell
# Proje klasörüne git
cd C:\Users\CEZ\Desktop\termProjectHavadurumu\weather-assistant

# PYTHONPATH'i ayarla ve backend'i başlat
$env:PYTHONPATH="src"
python src/server.py
```

**Çıktı:**
```
 * Running on http://0.0.0.0:8000
```

Backend şimdi `http://localhost:8000` adresinde çalışıyor!

### Yöntem 2: Flask CLI ile

```powershell
cd C:\Users\CEZ\Desktop\termProjectHavadurumu\weather-assistant
$env:PYTHONPATH="src"
python -m flask --app src.server run --host 0.0.0.0 --port 8000
```

---

## 2. Backend'i Test Etme

### Yöntem 1: Tarayıcıdan Test (Sadece GET istekleri için)

**Health Check:**
```
http://localhost:8000/health
```

Tarayıcıda açın, şunu göreceksiniz:
```json
{"status":"ok","model_loaded":true}
```

**Not:** POST istekleri için tarayıcı kullanılamaz, aşağıdaki yöntemleri kullanın.

---

### Yöntem 2: PowerShell ile Test (Windows için)

**Health Check:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Predict Endpoint (Konum ile):**
```powershell
$body = @{
    lat = 41.0082
    lon = 28.9784
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri http://localhost:8000/predict `
    -Method POST `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body $body `
    -UseBasicParsing

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

### Yöntem 3: Python Test Scripti ile (En Kolay)

**Test scriptini çalıştır:**
```powershell
python test_api.py
```

Bu script otomatik olarak tüm endpoint'leri test eder ve sonuçları gösterir.

---

### Yöntem 4: cURL ile (Eğer yüklüyse)

**Health Check:**
```powershell
curl.exe http://localhost:8000/health
```

**Predict Endpoint:**
```powershell
curl.exe -X POST http://localhost:8000/predict `
    -H "Content-Type: application/json" `
    -d '{\"lat\":41.0082,\"lon\":28.9784}'
```

---

### Yöntem 5: Postman veya Insomnia (Görsel Arayüz)

1. **Postman** veya **Insomnia** uygulamasını açın
2. Yeni bir **POST** request oluşturun
3. URL: `http://localhost:8000/predict`
4. Headers:
   - Key: `Content-Type`
   - Value: `application/json`
5. Body (raw JSON):
```json
{
  "lat": 41.0082,
  "lon": 28.9784
}
```
6. **Send** butonuna tıklayın

---

### Yöntem 6: HTML Test Sayfası (En Kolay Görsel Test)

`test.html` dosyasını tarayıcıda açın ve formu kullanın.

---

## 3. Örnek Request/Response

### Request (Konum ile):
```json
POST http://localhost:8000/predict
Content-Type: application/json

{
  "lat": 41.0082,
  "lon": 28.9784
}
```

### Response:
```json
{
  "success": true,
  "summary": "Hava yagmurlu, semsiye almayi unutmayin.",
  "recommendations": [
    {
      "id": "rain",
      "message": "Hava yagmurlu, semsiye almayi unutmayin.",
      "active": true
    },
    ...
  ],
  "features": {
    "temp": 17.3,
    "humidity": 88.0,
    ...
  },
  "meta": {
    "location_name": "Istanbul",
    "location_country": "Turkey",
    ...
  }
}
```

---

## 4. Backend'i Durdurma

Backend'i çalıştırdığınız terminal penceresinde:
- **Ctrl + C** tuşlarına basın

---

## 5. Sorun Giderme

### Backend başlamıyor:
```powershell
# Flask-CORS yüklü mü kontrol et
pip install flask-cors

# Tüm dependencies'i yükle
pip install -r requirements.txt
```

### Port 8000 kullanımda:
```powershell
# Farklı port kullan
python src/server.py
# Sonra server.py dosyasında port=8001 yap
```

### Model yüklenemiyor:
- `models/weather_model.pkl` dosyasının var olduğundan emin olun

---

## 6. Mobil Uygulama İçin Hazırlık

Backend hazır! Mobil uygulamanızdan şu şekilde kullanabilirsiniz:

**Base URL:** `http://localhost:8000` (local test için)
**Base URL:** `https://your-api.onrender.com` (production için)

**Endpoint:** `POST /predict`

**Request Body:**
```json
{
  "lat": <kullanıcının_latitude>,
  "lon": <kullanıcının_longitude>
}
```

