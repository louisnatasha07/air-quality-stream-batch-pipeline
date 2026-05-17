import json
import os
import psycopg2
from dotenv import load_dotenv
from kafka import KafkaConsumer

# --- SYSTEM INITIALIZATION ---
load_dotenv()

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVER', 'localhost:9092')
TOPIC_NAME = 'air_quality_stream'

# Loadout koneksi ke base camp PostgreSQL
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5555')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'Admin123')
DB_NAME = os.getenv('POSTGRES_DB', 'air_quality_pgsql')

def check_anomaly(payload):
    """Rule-based anomaly detection (Early Game Level).
    Mendeteksi hazard berdasarkan threshold polusi udara standar."""
    pm25 = payload.get('pm25') or 0
    aqi = payload.get('aqi') or 0
    
    # Threshold: PM2.5 > 50 atau AQI > 100 memicu alert anomali
    if pm25 > 50 or aqi > 100:
        return True, f"Hazard! PM2.5: {pm25}, AQI: {aqi}"
    return False, "Normal"

def sync_to_inventory(cursor, payload, is_anomaly, reason):
    """Menyimpan data hasil tangkapan ke dalam tabel PostgreSQL."""
    insert_query = """
        INSERT INTO air_quality_stream 
        (timestamp, latitude, longitude, pm25, pm10, carbon_monoxide, nitrogen_dioxide, sulphur_dioxide, ozone, aqi, is_anomaly, anomaly_reason)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    record = (
        payload['timestamp'], payload['latitude'], payload['longitude'],
        payload['pm25'], payload['pm10'], payload['carbon_monoxide'],
        payload['nitrogen_dioxide'], payload['sulphur_dioxide'], payload['ozone'],
        payload['aqi'], is_anomaly, reason
    )
    cursor.execute(insert_query, record)

def main():
    print("[SYSTEM BOOTING] Mengaktifkan Interceptor Consumer...")
    
    # 1. Buka jalur ke markas Database
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("[DB UPLINK] Sukses terhubung ke PostgreSQL.")
    except Exception as e:
        print(f"[CRITICAL ERROR] Gagal menembus Database: {e}")
        return

    # 2. Deploy Kafka Consumer
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    print(f"[INTERCEPTOR STANDBY] Menunggu aliran data di topic: {TOPIC_NAME}...\n")

    # 3. Looping intercept data (Endless Grind)
    try:
        for message in consumer:
            payload = message.value
            
            # Cek status debuff
            is_anomaly, reason = check_anomaly(payload)
            
            # Eksekusi sinkronisasi
            sync_to_inventory(cursor, payload, is_anomaly, reason)
            
            # Status log
            status_tag = "[! ANOMALI !]" if is_anomaly else "[NORMAL]"
            print(f"[{payload['timestamp']}] Tangkapan {status_tag} -> Tersimpan di database.")
            
    except KeyboardInterrupt:
        print("\n[SYSTEM SHUTDOWN] Memutus uplink...")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()