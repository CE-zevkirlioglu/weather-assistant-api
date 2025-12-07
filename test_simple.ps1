# Weather Assistant API - Basit Test Scripti
# PowerShell script - Çalıştırmak için: .\test_simple.ps1

$API_URL = "http://localhost:8000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Weather Assistant API Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Health Check
Write-Host "1. Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "$API_URL/health" -UseBasicParsing
    $healthJson = $health.Content | ConvertFrom-Json
    Write-Host "   Status: $($healthJson.status)" -ForegroundColor Green
    Write-Host "   Model Loaded: $($healthJson.model_loaded)" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: Backend çalışmıyor!" -ForegroundColor Red
    Write-Host "   Backend'i başlatmak için: python src/server.py" -ForegroundColor Yellow
    exit
}
Write-Host ""

# 2. Predict Test (İstanbul)
Write-Host "2. Predict Test (İstanbul koordinatları)..." -ForegroundColor Yellow
$body = @{
    lat = 41.0082
    lon = 28.9784
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$API_URL/predict" `
        -Method POST `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body $body `
        -UseBasicParsing
    
    $json = $response.Content | ConvertFrom-Json
    
    Write-Host "   ✅ Başarılı!" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Özet: $($json.summary)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Konum: $($json.meta.location_name), $($json.meta.location_country)" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "   Hava Durumu:" -ForegroundColor Yellow
    Write-Host "     🌡️  Sıcaklık: $($json.features.temp)°C"
    Write-Host "     💧 Nem: $($json.features.humidity)%"
    Write-Host "     💨 Rüzgar: $($json.features.wind_speed) m/s"
    Write-Host "     📊 Basınç: $($json.features.pressure) hPa"
    Write-Host "     ☁️  Bulutluluk: $($json.features.clouds)%"
    Write-Host "     ☀️  UV İndeksi: $($json.features.uv_index)"
    Write-Host ""
    
    $activeRecs = $json.recommendations | Where-Object { $_.active }
    if ($activeRecs) {
        Write-Host "   Aktif Öneriler:" -ForegroundColor Yellow
        foreach ($rec in $activeRecs) {
            Write-Host "     • $($rec.message)" -ForegroundColor Green
        }
    } else {
        Write-Host "   Aktif öneri yok." -ForegroundColor Gray
    }
    
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test tamamlandı!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

