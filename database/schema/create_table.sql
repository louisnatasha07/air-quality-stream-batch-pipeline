-- ============================================================
-- Air Quality Stream-Batch Pipeline Database Schema
-- ============================================================

-- ============================================================
-- STREAM PROCESSING TABLE
-- Source: Open-Meteo API via Kafka Producer and Consumer
-- ============================================================

CREATE TABLE IF NOT EXISTS air_quality_stream (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    city VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT,
    pm25 FLOAT,
    pm10 FLOAT,
    carbon_monoxide FLOAT,
    nitrogen_dioxide FLOAT,
    sulphur_dioxide FLOAT,
    ozone FLOAT,
    aqi FLOAT,
    is_anomaly BOOLEAN,
    anomaly_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- BATCH PROCESSING TABLES
-- Source: Copernicus CAMS via Dagster Batch Pipeline
-- Note:
-- These tables are usually created/updated automatically by
-- batch/main.py when the batch pipeline loads data to PostgreSQL.
-- ============================================================

CREATE TABLE IF NOT EXISTS cams_air_quality_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    timestamp TIMESTAMP,
    cams_pm2_5 FLOAT,
    cams_pm10 FLOAT,
    prediction FLOAT,
    is_anomaly BOOLEAN
);

CREATE TABLE IF NOT EXISTS city_air_quality_summary (
    city VARCHAR(100) PRIMARY KEY,
    average_pm25 FLOAT,
    max_pm25 FLOAT,
    avg_prediction FLOAT,
    anomaly_count INTEGER
);

-- ============================================================
-- OPTIONAL FUTURE TABLE
-- Used later for comparing batch prediction and stream actual data
-- ============================================================

CREATE TABLE IF NOT EXISTS forecast_comparison_results (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    comparison_time TIMESTAMP,
    predicted_pm25 FLOAT,
    actual_pm25 FLOAT,
    error_value FLOAT,
    absolute_error FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);