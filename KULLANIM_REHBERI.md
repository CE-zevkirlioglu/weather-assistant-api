# Weather Assistant - Kullanım Rehberi

Bu rehber, projeyi nasıl çalıştıracağınızı, test edeceğinizi ve deploy edeceğinizi gösterir.

---

## 📋 İçindekiler

1. [Kurulum](#kurulum)
2. [Backend'i Başlatma](#backendi-başlatma)
3. [Test Etme](#test-etme)
4. [Production Server](#production-server)
5. [Render.com'a Deploy](#rendercoma-deploy)
6. [Sorun Giderme](#sorun-giderme)

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.11+ (bkz. `runtime.txt`)
- WeatherAPI.com API key ([Ücretsiz alın](https://www.weatherapi.com/))

### Adımlar

```powershell
# 1. Proje klasörüne git
cd C:\Users\CEZ\Desktop\termProjectHavadurumu\weather-assistant

# 2. Virtual environment oluştur (önerilen)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Dependencies yükle
pip install -r requirements.txt

# 4. Environment variables ayarla
$env:WEATHER_API_KEY = "<your_weatherapi_key>"
$env:PYTHONPATH = "src"
```

---

## 🏃 Backend'i Başlatma

### Yöntem 1: Python ile (Önerilen)

```powershell
$env:PYTHONPATH="src"
python src/server.py
```

**Beklenen çıktı:**
```
 * Running on http://0.0.0.0:8000
 * Running on http://127.0.0.1:8000
```

⚠️ **Not:** "WARNING: This is a development server" uyarısı normaldir, local development için sorun değil.

### Yöntem 2: Batch Script

```powershell
.\start_backend.bat
```

### Yöntem 3: Flask CLI

```powershell
$env:PYTHONPATH="src"
python -m flask --app src.server run --host 0.0.0.0 --port 8000
```

**Backend şimdi `http://localhost:8000` adresinde çalışıyor!**

---

## 🧪 Test Etme

### Yöntem 1: Browser Test Interface (En Kolay) ⭐

1. Backend'i başlatın (yukarıdaki adımlardan biriyle)
2. `test.html` dosyasını tarayıcıda açın
3. Koordinatları girin (örnek: İstanbul için 41.0082, 28.9784)
4. "Hava Durumu Tahmini Al" butonuna tıklayın
5. Sonuçları görün!

### Yöntem 2: Python Test Scripti

```powershell
python test_api.py
```

Bu script otomatik olarak:
- ✅ Health check yapar
- ✅ Konum ile tahmin yapar
- ✅ Manuel feature'lar ile tahmin yapar
- ✅ Geçersiz koordinat kontrolü yapar

### Yöntem 3: PowerShell Komutları

**Health Check:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Predict Endpoint (İstanbul):**
```powershell
$body = '{"lat":41.0082,"lon":28.9784}'
Invoke-WebRequest -Uri http://localhost:8000/predict `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body `
    -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Farklı Şehirler:**
```powershell
# Ankara
$body = '{"lat":39.9334,"lon":32.8597}'
Invoke-WebRequest -Uri http://localhost:8000/predict -Method POST -Headers @{"Content-Type"="application/json"} -Body $body -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 10

# İzmir
$body = '{"lat":38.4192,"lon":27.1287}'
Invoke-WebRequest -Uri http://localhost:8000/predict -Method POST -Headers @{"Content-Type"="application/json"} -Body $body -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Yöntem 4: Tarayıcıdan (Sadece Health Check)

Tarayıcıda şu adresi açın:
```
http://localhost:8000/health
```

Beklenen çıktı:
```json
{"status":"ok","model_loaded":true}
```

### Yöntem 5: cURL (Eğer yüklüyse)

```powershell
# Health Check
curl.exe http://localhost:8000/health

# Predict
curl.exe -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"lat\":41.0082,\"lon\":28.9784}"
```

---

## 📊 Örnek Request/Response

### Request
```json
POST http://localhost:8000/predict
Content-Type: application/json

{
  "lat": 41.0082,
  "lon": 28.9784
}
```

### Response
```json
{
  "success": true,
  "summary": "Hava durumu oldukca guzel, tadini cikar.",
  "recommendations": [
    {
      "id": "hot",
      "message": "Hava cok sicak, ince giyin.",
      "active": false
    },
    {
      "id": "pleasant",
      "message": "Hava durumu oldukca guzel, tadini cikar.",
      "active": true
    }
  ],
  "features": {
    "temp": 17.3,
    "humidity": 88.0,
    "wind_speed": 1.61,
    "pressure": 1019.0,
    "clouds": 0.0,
    "uv_index": 0.0
  },
  "meta": {
    "location_name": "Istanbul",
    "location_country": "Turkey",
    "local_time": "2025-01-15 14:30",
    "source": "weatherapi"
  }
}
```

---

## 🏭 Production Server

### Development vs Production

**Development Server (Flask Built-in - Local için):**
- ✅ Hızlı geliştirme için ideal
- ✅ Otomatik reload
- ✅ Local test için yeterli
- ⚠️ "WARNING: This is a development server" uyarısı normaldir, sorun değil

**Production Server (Render.com'da otomatik):**
- ✅ Render.com deploy edildiğinde otomatik olarak Gunicorn kullanılır
- ✅ Güvenli ve optimize
- ✅ Multi-worker desteği
- ✅ Linux ortamında çalışır

**Not:** Local'de production server test etmeye gerek yok. Render.com'da deploy edildiğinde otomatik olarak production server kullanılacak.

---

## 🌐 Render.com'a Deploy

### Ön Gereksinimler
1. Render.com hesabı (ücretsiz plan yeterli)
2. GitHub repository'si
3. WeatherAPI.com API key'i

### Adımlar

#### 1. GitHub'a Push

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

#### 2. Render.com'da Web Service Oluştur

1. [Render.com Dashboard](https://dashboard.render.com) üzerinden giriş yapın
2. "New +" → "Web Service" seçin
3. GitHub repository'nizi bağlayın

#### 3. Environment Variables Ayarla

Render.com dashboard'unda "Environment" sekmesine gidin:

- **PYTHONPATH**: `src`
- **WEATHER_API_KEY**: WeatherAPI.com API key'iniz

#### 4. Deploy

Render.com otomatik olarak:
- ✅ `render.yaml` dosyasını algılar
- ✅ Dependencies'leri yükler (`requirements.txt`)
- ✅ Gunicorn ile production server başlatır

#### 5. Model Dosyasını Kontrol Et

`models/weather_model.pkl` dosyasının repository'de olduğundan emin olun:

```bash
git add models/weather_model.pkl
git commit -m "Add model file"
git push origin main
```

### Deploy Sonrası

API'niz şu URL'de olacak:
```
https://weather-assistant-api.onrender.com
```

**Test:**
```bash
curl https://weather-assistant-api.onrender.com/health
```

### Troubleshooting

**Model yüklenemiyor:**
- `models/weather_model.pkl` dosyasının repository'de olduğundan emin olun
- Render.com logs'larını kontrol edin

**WeatherAPI Key Hatası:**
- Environment variable'ın doğru ayarlandığından emin olun

**CORS Hataları:**
- CORS zaten aktif, `src/server.py` dosyasını kontrol edin

---

## 🛑 Backend'i Durdurma

Backend'i çalıştırdığınız terminal penceresinde:
- **Ctrl + C** tuşlarına basın

---

## 🔧 Sorun Giderme

### Backend başlamıyor

```powershell
# Dependencies kontrolü
pip install -r requirements.txt

# Flask-CORS kontrolü
pip install flask-cors
```

### Port 8000 kullanımda

```powershell
# Hangi process port 8000'i kullanıyor?
netstat -ano | findstr :8000

# Process'i sonlandır (PID'yi yukarıdaki komuttan alın)
taskkill /PID <PID_NUMARASI> /F
```

### Model yüklenemiyor

- `models/weather_model.pkl` dosyasının var olduğundan emin olun
- Dosya yolunu kontrol edin

### Connection refused hatası

- Backend'in çalıştığından emin olun
- Backend penceresinde hata mesajı var mı kontrol edin
- Port numarasını kontrol edin

### WeatherAPI hatası

- `WEATHER_API_KEY` environment variable'ının ayarlandığından emin olun
- API key'in geçerli olduğunu kontrol edin

---

## 📱 Mobil Uygulama İçin

Backend hazır! Mobil uygulamanızdan şu şekilde kullanabilirsiniz:

**Local Test:**
```
http://localhost:8000/predict
```

**Production:**
```
https://your-api.onrender.com/predict
```

**Request:**
```json
{
  "lat": <latitude>,
  "lon": <longitude>
}
```

Detaylı API dokümantasyonu için `API_DOCS.md` dosyasına bakın.

---

## 📝 Hızlı Başlangıç (Özet)

**Terminal 1 (Backend):**
```powershell
cd C:\Users\CEZ\Desktop\termProjectHavadurumu\weather-assistant
$env:PYTHONPATH="src"
python src/server.py
```

**Terminal 2 (Test):**
```powershell
# Yöntem 1: Browser
# test.html dosyasını aç

# Yöntem 2: Python script
python test_api.py

# Yöntem 3: PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```

**Veya sadece:**
```powershell
.\start_backend.bat
# Sonra test.html'i aç
```

---

## 📚 Ek Dokümantasyon

- **`SISTEM_AKISI.md`** - Sistemin nasıl çalıştığını detaylı açıklar
- **`API_DOCS.md`** - Tam API dokümantasyonu ve mobil entegrasyon örnekleri
- **`README.md`** - Proje genel bakışı

---

**Sorularınız için:** Proje dokümantasyonuna bakın veya issue açın.

