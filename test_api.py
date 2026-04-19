"""
API test scripti - Mobil uygulama entegrasyonu için örnek kullanım
"""
import requests
import json

# API Base URL - Render.com deploy sonrası buraya URL'nizi yazın
API_BASE_URL = "http://localhost:8000"  # Local test için
# API_BASE_URL = "https://weather-assistant-api.onrender.com"  # Production için

def test_health():
    """Health check endpoint testi"""
    print("Testing /health endpoint...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_predict_with_location():
    """Konum ile tahmin testi (Mobil uygulama senaryosu)"""
    print("Testing /predict endpoint with location...")
    
    # İstanbul koordinatları
    payload = {
        "lat": 41.0082,
        "lon": 28.9784
    }
    
    response = requests.post(
        f"{API_BASE_URL}/predict",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Summary: {data.get('summary')}")
        print(f"Location: {data.get('meta', {}).get('location_name')}")
        print(f"Active Recommendations:")
        for rec in data.get('recommendations', []):
            if rec.get('active'):
                print(f"  - {rec.get('message')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_predict_with_features():
    """Manuel feature'lar ile tahmin testi"""
    print("Testing /predict endpoint with manual features...")
    
    payload = {
        "features": {
            "temp": 25,
            "humidity": 60,
            "wind_speed": 5,
            "pressure": 1013,
            "clouds": 30,
            "uv_index": 6
        }
    }
    
    response = requests.post(
        f"{API_BASE_URL}/predict",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Summary: {data.get('summary')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_invalid_coordinates():
    """Geçersiz koordinat testi"""
    print("Testing /predict endpoint with invalid coordinates...")
    
    payload = {
        "lat": 100,  # Geçersiz (90'dan büyük)
        "lon": 200   # Geçersiz (180'den büyük)
    }
    
    response = requests.post(
        f"{API_BASE_URL}/predict",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("Weather Assistant API Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_health()
        test_predict_with_location()
        test_predict_with_features()
        test_invalid_coordinates()
        
        print("=" * 50)
        print("All tests completed!")
        print("=" * 50)
    except requests.exceptions.ConnectionError:
        print("ERROR: API'ye bağlanılamadı. Servisin çalıştığından emin olun.")
        print(f"Expected URL: {API_BASE_URL}")
    except Exception as e:
        print(f"ERROR: {e}")

