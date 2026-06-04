import json
import time
import requests
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from kafka import KafkaProducer

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- SYSTEM INITIALIZATION ---
load_dotenv()

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVER', 'kafka:29092')
API_URL = os.getenv('OPEN_METEO_API', 'https://air-quality-api.open-meteo.com/v1/air-quality')
TOPIC_NAME = 'air_quality_stream'

# 4 Cities untuk monitoring (3 untuk sinkron dengan batch + 1 lokal)
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
    },
    {
        "city": "Surakarta",
        "latitude": -7.5561,
        "longitude": 110.8317
    }
]

def fetch_telemetry_data(city_data, retries=3):
    """Fetch data dari Open-Meteo API dengan retry dan timeout."""
    params = {
        "latitude": city_data["latitude"],
        "longitude": city_data["longitude"],
        "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
        "timezone": "auto"
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if "current" not in data:
                raise ValueError("Field 'current' tidak ditemukan di response API")

            return data

        except Exception as e:
            print(
                f"[API ERROR] {city_data['city']} attempt {attempt}/{retries}: {e}"
            )

            if attempt == retries:
                return None

            time.sleep(2 ** attempt)

def fetch_and_send(city_data, producer):
    """
    Fetch data untuk 1 city dan langsung kirim ke Kafka.
    Function ini akan dijalankan parallel untuk semua cities.
    """
    raw_data = fetch_telemetry_data(city_data)
    
    if raw_data and 'current' in raw_data:
        current = raw_data['current']
        
        # Formatting payload
        payload = {
            "timestamp": current.get('time'),
            "city": city_data["city"],
            "latitude": city_data["latitude"],
            "longitude": city_data["longitude"],
            "pm25": current.get('pm2_5'),
            "pm10": current.get('pm10'),
            "carbon_monoxide": current.get('carbon_monoxide'),
            "nitrogen_dioxide": current.get('nitrogen_dioxide'),
            "sulphur_dioxide": current.get('sulphur_dioxide'),
            "ozone": current.get('ozone'),
            "aqi": current.get('us_aqi')
        }
        
        # Kirim ke Kafka
        producer.send(TOPIC_NAME, value=payload).get(timeout=10)
        
        return {
            "city": city_data["city"],
            "pm25": payload['pm25'],
            "aqi": payload['aqi'],
            "timestamp": payload['timestamp'],
            "success": True
        }
    else:
        return {
            "city": city_data["city"],
            "success": False
        }

def main():
    # Inisialisasi Vanguard Producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"[SYSTEM READY] Vanguard Producer standby. Mengunci target topic: {TOPIC_NAME}")
    print("[UPLINK ESTABLISHED] Memulai transmisi data stream...")
    print(f"[MONITORING] {len(CITIES)} cities: {', '.join([c['city'] for c in CITIES])}")
    print("[MODE] Parallel fetching - semua cities sekaligus")
    print()
    
    while True:
        start_time = time.time()
        
        # Fetch semua cities secara parallel menggunakan ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(CITIES)) as executor:
            # Submit semua tasks
            futures = {
                executor.submit(fetch_and_send, city, producer): city 
                for city in CITIES
            }
            
            # Collect results as they complete
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
            
            # Sort results by city name untuk display yang konsisten
            results.sort(key=lambda x: x['city'])
            
            # Print results
            for result in results:
                if result['success']:
                    print(f"[{result['city']:15}] PM2.5: {result['pm25']:6.1f} | AQI: {result['aqi']:4} | {result['timestamp']}")
                else:
                    print(f"[{result['city']:15}] FAILED to fetch data")
        
        elapsed = time.time() - start_time
        print(f"[BATCH COMPLETE] {len(CITIES)} cities fetched in {elapsed:.2f}s")
        print()
        
        # Cooldown sebelum batch berikutnya (5 detik)
        time.sleep(5)

if __name__ == "__main__":
    main()