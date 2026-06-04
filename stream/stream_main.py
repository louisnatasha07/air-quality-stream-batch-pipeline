"""
Stream Processing Main Orchestrator
Menjalankan producer dan consumer secara bersamaan
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class StreamOrchestrator:
    """
    Orchestrator untuk menjalankan stream processing pipeline
    """
    
    def __init__(self):
        self.producer_process = None
        self.consumer_process = None
        self.running = False
        
        # Setup signal handler untuk graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """
        Start producer dan consumer
        """
        print("=" * 60)
        print("🚀 AIR QUALITY STREAM PROCESSING PIPELINE")
        print("=" * 60)
        print()
        
        # Check prerequisites
        if not self._check_prerequisites():
            print("❌ Prerequisites check failed. Exiting...")
            return
        
        print("✅ Prerequisites check passed")
        print()
        
        # Start producer
        print("📡 Starting Producer...")
        producer_script = PROJECT_ROOT / "stream" / "producer" / "producer.py"
        self.producer_process = subprocess.Popen(
            [sys.executable, str(producer_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        time.sleep(3)
        
        # Check if producer started successfully
        if self.producer_process.poll() is not None:
            print("❌ Producer failed to start")
            return
        
        print("✅ Producer started")
        print()
        
        # Start consumer
        print("📥 Starting Consumer...")
        consumer_script = PROJECT_ROOT / "stream" / "consumer" / "consumer.py"
        self.consumer_process = subprocess.Popen(
            [sys.executable, str(consumer_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        time.sleep(3)
        
        # Check if consumer started successfully
        if self.consumer_process.poll() is not None:
            print("❌ Consumer failed to start")
            self.stop()
            return
        
        print("✅ Consumer started")
        print()
        
        print("=" * 60)
        print("🎯 Stream Pipeline Running")
        print("=" * 60)
        print("Press Ctrl+C to stop")
        print()
        
        self.running = True
        
        # Monitor processes
        self._monitor_processes()
    
    def _check_prerequisites(self):
        """
        Check apakah semua prerequisites terpenuhi
        """
        checks = []
        
        # Check Kafka
        print("Checking Kafka connection...")
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVER', 'localhost:9092'),
                request_timeout_ms=5000
            )
            producer.close()
            checks.append(True)
            print("  ✓ Kafka accessible")
        except Exception as e:
            print(f"  ✗ Kafka not accessible: {e}")
            checks.append(False)
        
        # Check PostgreSQL
        print("Checking PostgreSQL connection...")
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'postgres_db'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'Shantvl07'),
                dbname=os.getenv('POSTGRES_DB', 'air_quality_db'),
                connect_timeout=5
            )
            conn.close()
            checks.append(True)
            print("  ✓ PostgreSQL accessible")
        except Exception as e:
            print(f"  ✗ PostgreSQL not accessible: {e}")
            checks.append(False)
        
        # Check Open-Meteo API
        print("Checking Open-Meteo API...")
        try:
            import requests
            response = requests.get(
                "https://air-quality-api.open-meteo.com/v1/air-quality",
                params={"latitude": -7.5561, "longitude": 110.8317, "current": "pm2_5"},
                timeout=5
            )
            checks.append(response.status_code == 200)
            print("  ✓ Open-Meteo API accessible")
        except Exception as e:
            print(f"  ✗ Open-Meteo API not accessible: {e}")
            checks.append(False)
        
        return all(checks)
    
    def _monitor_processes(self):
        """
        Monitor producer dan consumer processes
        """
        try:
            while self.running:
                # Check if processes are still running
                producer_status = self.producer_process.poll()
                consumer_status = self.consumer_process.poll()
                
                if producer_status is not None:
                    print(f"\n⚠️  Producer stopped unexpectedly (exit code: {producer_status})")
                    # Print stderr if available
                    if self.producer_process.stderr:
                        stderr = self.producer_process.stderr.read()
                        if stderr:
                            print(f"Producer Error:\n{stderr}")
                    self.stop()
                    break
                
                if consumer_status is not None:
                    print(f"\n⚠️  Consumer stopped unexpectedly (exit code: {consumer_status})")
                    # Print stderr if available
                    if self.consumer_process.stderr:
                        stderr = self.consumer_process.stderr.read()
                        if stderr:
                            print(f"Consumer Error:\n{stderr}")
                    self.stop()
                    break
                
                # Sleep longer to avoid busy waiting
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Shutdown signal received...")
            self.stop()
    
    def stop(self):
        """
        Stop producer dan consumer gracefully
        """
        self.running = False
        
        print("\n" + "=" * 60)
        print("🛑 Stopping Stream Pipeline...")
        print("=" * 60)
        
        if self.producer_process:
            print("Stopping Producer...")
            self.producer_process.terminate()
            try:
                self.producer_process.wait(timeout=5)
                print("  ✓ Producer stopped")
            except subprocess.TimeoutExpired:
                print("  ⚠️  Force killing Producer...")
                self.producer_process.kill()
        
        if self.consumer_process:
            print("Stopping Consumer...")
            self.consumer_process.terminate()
            try:
                self.consumer_process.wait(timeout=5)
                print("  ✓ Consumer stopped")
            except subprocess.TimeoutExpired:
                print("  ⚠️  Force killing Consumer...")
                self.consumer_process.kill()
        
        print("\n✅ Stream Pipeline stopped successfully")
        print("=" * 60)
    
    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals
        """
        self.stop()
        sys.exit(0)


def main():
    """
    Main entry point
    """
    orchestrator = StreamOrchestrator()
    orchestrator.start()


if __name__ == "__main__":
    main()
