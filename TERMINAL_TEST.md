# Terminal'de Test Etme Rehberi

Bu rehber, Weather Assistant API'sini terminalden adım adım nasıl test edeceğinizi gösterir.

## 📋 Adım Adım Komutlar

### 1️⃣ Backend'i Başlatma

**Yeni bir PowerShell penceresi açın ve şu komutları sırayla çalıştırın:**

```powershell
# 1. Proje klasörüne git
cd C:\Users\CEZ\Desktop\termProjectHavadurumu\weather-assistant

# 2. PYTHONPATH'i ayarla
$env:PYTHONPATH="src"

# 3. Backend'i başlat
python src/server.py
```

**Beklenen çıktı:**
```
 * Running on http://0.0.0.0:8000
 * Running on http://127.0.0.1:8000
```

✅ **Backend şimdi çalışıyor!** Bu pencereyi açık bırakın.

---

### 2️⃣ Yeni Bir Terminal Penceresi Açın

**Backend çalışırken, yeni bir PowerShell penceresi açın** (ilk pencereyi kapatmayın!)

---

### 3️⃣ Health Check Testi

**Yeni terminalde:**

```powershell
# Proje klasörüne git
cd C:\Users\CEZ\Desktop\termProjectHavadurumu\weather-assistant

# Health check yap
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Beklenen çıktı:**
```json
{"status":"ok","model_loaded":true}
```

✅ **Backend çalışıyor ve model yüklü!**

---

### 4️⃣ Predict Endpoint Testi (Konum ile)

**Aynı terminalde:**

```powershell
# İstanbul koordinatları ile test
$body = @{
    lat = 41.0082
    lon = 28.9784
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri http://localhost:8000/predict `
    -Method POST `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body $body `
    -UseBasicParsing

# Sonucu güzel formatta göster
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Beklenen çıktı:**
```json
{
    "success": true,
    "summary": "Hava durumu oldukca guzel, tadini cikar.",
    "features": {
        "temp": 17.3,
        "humidity": 88.0,
        ...
    },
    "recommendations": [...],
    "meta": {
        "location_name": "Istanbul",
        ...
    }
}
```

✅ **API çalışıyor ve gerçek hava durumu verileri alınıyor!**

---

### 5️⃣ Farklı Koordinatlar ile Test

**Aynı terminalde farklı şehirler test edebilirsiniz:**

```powershell
# Ankara koordinatları
$body = @{
    lat = 39.9334
    lon = 32.8597
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri http://localhost:8000/predict `
    -Method POST `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body $body `
    -UseBasicParsing

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

```powershell
# İzmir koordinatları
$body = @{
    lat = 38.4192
    lon = 27.1287
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri http://localhost:8000/predict `
    -Method POST `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body $body `
    -UseBasicParsing

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

### 6️⃣ Python Test Scripti ile Test

**Daha kolay test için:**

```powershell
# Python test scriptini çalıştır
python test_api.py
```

Bu script otomatik olarak:
- ✅ Health check yapar
- ✅ Konum ile tahmin yapar
- ✅ Manuel feature'lar ile tahmin yapar
- ✅ Geçersiz koordinat kontrolü yapar

---

### 7️⃣ Backend'i Durdurma

**Backend'i çalıştırdığınız ilk terminal penceresinde:**
- `Ctrl + C` tuşlarına basın

---

## 🎯 Hızlı Test Komutları (Kopyala-Yapıştır)

### Tek Satırda Health Check:
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

### Tek Satırda Predict (İstanbul):
```powershell
Invoke-WebRequest -Uri http://localhost:8000/predict -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"lat":41.0082,"lon":28.9784}' -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 🔍 Detaylı Response Görmek İçin

```powershell
$body = '{"lat":41.0082,"lon":28.9784}'
$response = Invoke-WebRequest -Uri http://localhost:8000/predict -Method POST -Headers @{"Content-Type"="application/json"} -Body $body -UseBasicParsing
$json = $response.Content | ConvertFrom-Json

# Sadece özet mesajı göster
Write-Host "Özet: $($json.summary)" -ForegroundColor Green

# Sadece aktif önerileri göster
Write-Host "`nAktif Öneriler:" -ForegroundColor Yellow
$json.recommendations | Where-Object { $_.active } | ForEach-Object {
    Write-Host "  - $($_.message)" -ForegroundColor Cyan
}

# Konum bilgisi
Write-Host "`nKonum: $($json.meta.location_name), $($json.meta.location_country)" -ForegroundColor Magenta

# Hava durumu verileri
Write-Host "`nHava Durumu:" -ForegroundColor Yellow
Write-Host "  Sıcaklık: $($json.features.temp)°C"
Write-Host "  Nem: $($json.features.humidity)%"
Write-Host "  Rüzgar: $($json.features.wind_speed) m/s"
```

---

## ⚠️ Sorun Giderme

### Backend başlamıyor:
```powershell
# Flask-CORS yüklü mü kontrol et
pip install flask-cors

# Tüm dependencies'i yükle
pip install -r requirements.txt
```

### Port 8000 kullanımda:
```powershell
# Hangi process port 8000'i kullanıyor?
netstat -ano | findstr :8000

# Process'i sonlandır (PID'yi yukarıdaki komuttan alın)
taskkill /PID <PID_NUMARASI> /F
```

### Connection refused hatası:
- Backend'in çalıştığından emin olun (ilk terminal penceresini kontrol edin)
- Backend penceresinde hata mesajı var mı kontrol edin

---

## 📝 Özet: Minimum Test Komutları

**Terminal 1 (Backend):**
```powershell
cd C:\Users\CEZ\Desktop\termProjectHavadurumu\weather-assistant
$env:PYTHONPATH="src"
python src/server.py
```

**Terminal 2 (Test):**
```powershell
cd C:\Users\CEZ\Desktop\termProjectHavadurumu\weather-assistant
python test_api.py
```

Bu kadar! 🎉

