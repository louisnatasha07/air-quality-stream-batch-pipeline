"""
Dagster Orchestrator - Unified Control for Batch & Stream Pipelines
Buka Dagster UI: http://localhost:3000
"""

from dagster import (
    job, op, schedule, sensor, RunRequest, SkipReason,
    Definitions, DefaultSensorStatus
)
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


# ============================================
# BATCH PIPELINE OPERATIONS
# ============================================

@op
def batch_fetch_data():
    """Fetch historical data from Open-Meteo and CAMS"""
    print("📥 Fetching batch data...")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "batch" / "data_ingestion" / "openmeteo_batch.py")])
    return "Batch data fetched"


@op
def batch_preprocess(context, data_status):
    """Clean and preprocess data"""
    print("🧹 Preprocessing data...")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "batch" / "preprocessing" / "clean_data.py")])
    return "Data preprocessed"


@op
def batch_train_model(context, preprocessed_status):
    """Train ML model"""
    print("🤖 Training model...")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "batch" / "training" / "train_model.py")])
    return "Model trained"


@job(description="Batch Pipeline - Historical data processing & ML training")
def batch_pipeline():
    """Complete batch pipeline"""
    data = batch_fetch_data()
    preprocessed = batch_preprocess(data)
    batch_train_model(preprocessed)


@schedule(
    cron_schedule="0 1 * * *",  # Every day at 1am
    job=batch_pipeline,
    description="Run batch pipeline daily at 1am"
)
def daily_batch_schedule():
    """Daily batch processing schedule"""
    return {}


# ============================================
# STREAM PIPELINE OPERATIONS
# ============================================

@op
def start_stream_pipeline():
    """Start stream processing (producer + consumer)"""
    print("🚀 Starting stream pipeline...")
    print("📡 Producer and Consumer will run continuously")
    
    # Run stream orchestrator
    # Note: This is a long-running process, will keep Dagster job running
    subprocess.run([
        sys.executable, 
        str(PROJECT_ROOT / "stream" / "stream_main.py")
    ])
    
    return "Stream pipeline started"


@job(description="Stream Pipeline - Real-time data processing")
def stream_pipeline():
    """Stream processing pipeline"""
    start_stream_pipeline()


# ============================================
# UNIFIED OPERATIONS
# ============================================

@op
def run_batch():
    """Trigger batch pipeline"""
    subprocess.run([sys.executable, str(PROJECT_ROOT / "batch" / "main.py")])
    return "Batch completed"


@op
def run_stream(context, batch_status):
    """Start stream after batch completes"""
    print("⚡ Starting stream services...")
    
    # Start producer in background
    subprocess.Popen([
        sys.executable,
        str(PROJECT_ROOT / "stream" / "producer" / "producer.py")
    ])
    
    # Start consumer in background
    subprocess.Popen([
        sys.executable,
        str(PROJECT_ROOT / "stream" / "consumer" / "consumer.py")
    ])
    
    return "Stream services started in background"


@job(description="Run ALL Pipelines - Batch first, then Stream")
def run_all_pipelines():
    """Run batch pipeline, then start stream services"""
    batch_status = run_batch()
    run_stream(batch_status)


# ============================================
# SENSORS (Advanced - Optional)
# ============================================

@sensor(
    job=batch_pipeline,
    default_status=DefaultSensorStatus.STOPPED,
    description="Trigger batch when new data is available"
)
def new_data_sensor():
    """Check if new data is available and trigger batch pipeline"""
    # Example: Check if new files exist, or API has new data
    # For now, just skip
    return SkipReason("No new data detected")


# ============================================
# DAGSTER DEFINITIONS
# ============================================

defs = Definitions(
    jobs=[
        batch_pipeline,
        stream_pipeline,
        run_all_pipelines
    ],
    schedules=[
        daily_batch_schedule
    ],
    sensors=[
        new_data_sensor
    ]
)


# ============================================
# HOW TO USE
# ============================================
"""
1. Install Dagster:
   pip install dagster dagster-webserver

2. Start Dagster UI:
   dagster dev -f dagster_orchestrator.py

3. Open browser:
   http://localhost:3000

4. In Dagster UI:
   - Click "Launchpad" tab
   - Select job:
     • batch_pipeline: Run batch processing
     • stream_pipeline: Start stream services
     • run_all_pipelines: Run everything
   - Click "Launch Run"

5. Voila! 🎉
"""
