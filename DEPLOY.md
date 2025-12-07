# Render.com Deployment Guide

Bu rehber, Weather Assistant API'sini Render.com üzerinde deploy etmek için adımları içerir.

## Ön Gereksinimler

1. Render.com hesabı (ücretsiz plan yeterli)
2. GitHub repository'si (kodunuzun push edilmiş olması gerekir)
3. WeatherAPI.com API key'i

## Deployment Adımları

### 1. GitHub'a Kod Push Etme

```bash
git add .
git commit -m "Add Render.com deployment configuration"
git push origin main
```

### 2. Render.com'da Yeni Web Service Oluşturma

1. [Render.com Dashboard](https://dashboard.render.com) üzerinden giriş yapın
2. "New +" butonuna tıklayın
3. "Web Service" seçeneğini seçin
4. GitHub repository'nizi bağlayın veya manuel olarak URL girin

### 3. Service Ayarları

Render.com otomatik olarak `render.yaml` dosyasını algılayacaktır. Eğer manuel ayar yapmak isterseniz:

**Service Name:** `weather-assistant-api`

**Environment:** `Python 3`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn --chdir src server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### 4. Environment Variables Ayarlama

Render.com dashboard'unda "Environment" sekmesine gidin ve şu değişkenleri ekleyin:

- **PYTHONPATH**: `src`
- **WEATHER_API_KEY**: WeatherAPI.com'dan aldığınız API key'iniz

### 5. Deploy

"Create Web Service" butonuna tıklayın. Render.com otomatik olarak:
1. Repository'nizi clone edecek
2. Dependencies'leri yükleyecek
3. Servisi başlatacak

### 6. Model Dosyasını Kontrol Etme

Deploy sırasında `models/weather_model.pkl` dosyasının repository'de olduğundan emin olun. Eğer yoksa:

```bash
# Model dosyasını repository'ye ekleyin
git add models/weather_model.pkl
git commit -m "Add trained model"
git push origin main
```

## API Endpoint'leri

Deploy sonrası API'niz şu URL'de olacak:
```
https://weather-assistant-api.onrender.com
```

### Health Check
```bash
GET https://weather-assistant-api.onrender.com/health
```

### Predict Endpoint (Mobil Uygulama İçin)
```bash
POST https://weather-assistant-api.onrender.com/predict
Content-Type: application/json

{
  "lat": 41.0082,
  "lon": 28.9784
}
```

## Troubleshooting

### Model Yüklenemiyor

Eğer `/health` endpoint'i `"model_loaded": false` döndürüyorsa:

1. `models/weather_model.pkl` dosyasının repository'de olduğundan emin olun
2. Render.com logs'larını kontrol edin
3. Model dosyasının boyutunu kontrol edin (Render.com ücretsiz planında dosya boyutu limiti olabilir)

### CORS Hataları

CORS zaten yapılandırılmış durumda. Eğer hala sorun yaşıyorsanız, `src/server.py` dosyasındaki CORS ayarlarını kontrol edin.

### WeatherAPI Key Hatası

`WEATHER_API_KEY` environment variable'ının doğru ayarlandığından emin olun. Render.com dashboard'unda "Environment" sekmesinden kontrol edebilirsiniz.

## Mobil Uygulama Entegrasyonu

Mobil uygulamanızdan API'yi kullanmak için:

```javascript
// Örnek: React Native / JavaScript
const response = await fetch('https://weather-assistant-api.onrender.com/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    lat: userLatitude,
    lon: userLongitude
  })
});

const data = await response.json();
console.log(data.summary); // "Hava durumu oldukca guzel, tadini cikar."
console.log(data.recommendations); // Aktif öneriler listesi
```

## Monitoring

Render.com dashboard'unda:
- **Logs**: Real-time log görüntüleme
- **Metrics**: CPU, Memory kullanımı
- **Events**: Deploy geçmişi

## Notlar

- Render.com ücretsiz planında servisler 15 dakika inactivity sonrası sleep moduna geçer
- İlk request biraz yavaş olabilir (cold start)
- Production için Render.com'un ücretli planını kullanmanız önerilir

