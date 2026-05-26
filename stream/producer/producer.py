import json
import time
import requests
import os
import sys
from dotenv import load_dotenv
from kafka import KafkaProducer

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- SYSTEM INITIALIZATION ---
load_dotenv()

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVER', 'localhost:9092')
API_URL = os.getenv('OPEN_METEO_API', 'https://air-quality-api.open-meteo.com/v1/air-quality')
TOPIC_NAME = 'air_quality_stream'

# 3 Cities untuk sinkron dengan batch processing
CITIES = [
    {
        "city": "Jakarta",
        "latitude": -6.2088,
        "longitude": 106.8456
    },
    {
        "city": "Kuala Lumpur",
        "latitude": 3.1390,
        "longitude": 101.6869
    },
    {
        "city": "Singapore",
        "latitude": 1.3521,
        "longitude": 103.8198
    }
]

def fetch_telemetry_data(city_data):
    """Scouting data dari Open-Meteo API untuk city tertentu."""
    params = {
        "latitude": city_data["latitude"],
        "longitude": city_data["longitude"],
        "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[SYSTEM ERROR] Gagal menembus API untuk {city_data['city']}. Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"[CRITICAL ERROR] Koneksi terputus: {e}")
        return None

def main():
    # Inisialisasi Vanguard Producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"[SYSTEM READY] Vanguard Producer standby. Mengunci target topic: {TOPIC_NAME}")
    print("[UPLINK ESTABLISHED] Memulai transmisi data stream...")
    print(f"[MONITORING] {len(CITIES)} cities: {', '.join([c['city'] for c in CITIES])}")
    print()
    
    city_index = 0
    
    while True:
        # Rotate cities (Jakarta → KL → Singapore → Jakarta → ...)
        current_city = CITIES[city_index]
        
        raw_data = fetch_telemetry_data(current_city)
        
        if raw_data and 'current' in raw_data:
            current = raw_data['current']
            
            # Formatting payload agar sinkron dengan skema database
            payload = {
                "timestamp": current.get('time'),
                "city": current_city["city"],
                "latitude": current_city["latitude"],
                "longitude": current_city["longitude"],
                "pm25": current.get('pm2_5'),
                "pm10": current.get('pm10'),
                "carbon_monoxide": current.get('carbon_monoxide'),
                "nitrogen_dioxide": current.get('nitrogen_dioxide'),
                "sulphur_dioxide": current.get('sulphur_dioxide'),
                "ozone": current.get('ozone'),
                "aqi": current.get('us_aqi')
            }
            
            # Tembakkan payload ke Kafka
            producer.send(TOPIC_NAME, value=payload)
            print(f"[{current_city['city']:15}] PM2.5: {payload['pm25']:6.1f} | AQI: {payload['aqi']:4} | {payload['timestamp']}")
        
        # Rotate ke city berikutnya
        city_index = (city_index + 1) % len(CITIES)
        
        # Cooldown skill sebelum scouting berikutnya (5 detik)
        time.sleep(5)

if __name__ == "__main__":
    main()