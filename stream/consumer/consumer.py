import json
import os
import sys
from pathlib import Path
import psycopg2
import time
from dotenv import load_dotenv
from kafka import KafkaConsumer

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import Telegram alerter with error handling
try:
    from stream.alerting.telegram_alert import alerter
    TELEGRAM_ENABLED = True
except Exception as e:
    print(f"[WARNING] Telegram alert disabled: {e}")
    TELEGRAM_ENABLED = False
    alerter = None

# --- SYSTEM INITIALIZATION ---
load_dotenv()

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVER', 'kafka:29092')
TOPIC_NAME = 'air_quality_stream'
CONSUMER_GROUP = 'air_quality_consumer_group'  # Prevent duplicate consumers
EXPECTED_CITIES = 4  # Jumlah cities yang di-pull producer per cycle
MESSAGE_TIMEOUT = 10  # Timeout untuk tunggu semua cities (detik)

# Loadout koneksi ke base camp PostgreSQL
DB_HOST = os.getenv('POSTGRES_HOST', 'postgres_db')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'Shantvl07')
DB_NAME = os.getenv('POSTGRES_DB', 'air_quality_db')

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
        (timestamp, city, latitude, longitude, pm25, pm10, carbon_monoxide, nitrogen_dioxide, sulphur_dioxide, ozone, aqi, is_anomaly, anomaly_reason)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    record = (
        payload['timestamp'], payload.get('city', 'Unknown'), payload['latitude'], payload['longitude'],
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
        group_id=CONSUMER_GROUP,  # Important: prevent duplicate reads
        auto_offset_reset='latest',
        enable_auto_commit=True,
        consumer_timeout_ms=MESSAGE_TIMEOUT * 1000,  # Timeout untuk batch detection
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    print(f"[INTERCEPTOR STANDBY] Menunggu aliran data di topic: {TOPIC_NAME}...")
    print(f"[STRATEGY] Event-based notification - kirim setiap {EXPECTED_CITIES} cities processed\n")

    # 3. Looping intercept data (Endless Grind)
    cycle_count = 0
    try:
        while True:
            batch_start_time = time.time()
            messages_in_batch = 0
            
            # Collect messages sampai timeout atau dapat EXPECTED_CITIES
            for message in consumer:
                payload = message.value
                
                # Cek status debuff
                is_anomaly, reason = check_anomaly(payload)
                
                # Eksekusi sinkronisasi
                sync_to_inventory(cursor, payload, is_anomaly, reason)
                
                # Status log
                city = payload.get('city', 'Unknown')
                status_tag = "[! ANOMALI !]" if is_anomaly else "[NORMAL]"
                print(f"[{city:15}] {status_tag} PM2.5: {payload.get('pm25', 0):.1f} | AQI: {payload.get('aqi', 0)} -> DB")
                
                # Tambahkan ke batch buffer (tidak langsung kirim)
                if TELEGRAM_ENABLED and alerter:
                    alerter.add_to_batch(payload, reason)
                
                messages_in_batch += 1
                
                # Kalau sudah dapat EXPECTED_CITIES, kirim notif
                if messages_in_batch >= EXPECTED_CITIES:
                    break
            
            # Kirim batch notification setelah dapat semua cities
            if messages_in_batch > 0:
                cycle_count += 1
                elapsed = time.time() - batch_start_time
                print(f"\n[CYCLE #{cycle_count}] Processed {messages_in_batch} cities in {elapsed:.2f}s")
                
                if TELEGRAM_ENABLED and alerter:
                    alerter.send_batch_summary()
                    print(f"[TELEGRAM] Notification sent for cycle #{cycle_count}\n")
                else:
                    print()
            
    except KeyboardInterrupt:
        print("\n[SYSTEM SHUTDOWN] Memutus uplink...")
    finally:
        # Send remaining batch before shutdown
        if TELEGRAM_ENABLED and alerter:
            alerter.send_batch_summary()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()