import json
import time
import requests
import os
from dotenv import load_dotenv
from kafka import KafkaProducer

# --- SYSTEM INITIALIZATION ---
load_dotenv()

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVER', 'localhost:9092')
API_URL = os.getenv('OPEN_METEO_API', 'https://air-quality-api.open-meteo.com/v1/air-quality')
TOPIC_NAME = 'air_quality_stream'

# Koordinat Area Surakarta sebagai initial waypoint
LATITUDE = -7.5561
LONGITUDE = 110.8317

def fetch_telemetry_data():
    """Scouting data dari Open-Meteo API."""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
        "timezone": "Asia/Jakarta"
    }
    
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[SYSTEM ERROR] Gagal menembus API. Status Code: {response.status_code}")
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
    
    while True:
        raw_data = fetch_telemetry_data()
        
        if raw_data and 'current' in raw_data:
            current = raw_data['current']
            
            # Formatting payload agar sinkron dengan skema database
            payload = {
                "timestamp": current.get('time'),
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
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
            print(f"[PAYLOAD SENT] Waktu: {payload['timestamp']} | PM2.5: {payload['pm25']} | AQI: {payload['aqi']}")
        
        # Cooldown skill sebelum scouting berikutnya (10 detik)
        time.sleep(10)

if __name__ == "__main__":
    main()