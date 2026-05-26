"""
Quick script untuk truncate table air_quality_stream
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5555')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'Admin123')
DB_NAME = os.getenv('POSTGRES_DB', 'air_quality_pgsql')

try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Count data sebelum truncate
    cursor.execute("SELECT COUNT(*) FROM air_quality_stream")
    count_before = cursor.fetchone()[0]
    print(f"📊 Data sebelum truncate: {count_before} rows")
    
    # Truncate table
    cursor.execute("TRUNCATE TABLE air_quality_stream RESTART IDENTITY CASCADE")
    print("🗑️  Table air_quality_stream berhasil di-truncate!")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM air_quality_stream")
    count_after = cursor.fetchone()[0]
    print(f"✅ Data setelah truncate: {count_after} rows")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
