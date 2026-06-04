from sqlalchemy import text
from database.db_connection import engine

QUERY = """
CREATE TABLE IF NOT EXISTS forecast_comparison_results (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    batch_time TIMESTAMP,
    stream_time TIMESTAMP,
    comparison_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    predicted_pm25 FLOAT,
    actual_pm25 FLOAT,
    error_value FLOAT,
    absolute_error FLOAT,
    source_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

TRUNCATE TABLE forecast_comparison_results;

WITH batch_latest AS (
    SELECT DISTINCT ON (city)
        city,
        timestamp AS batch_time,
        predicted_pm2_5 AS predicted_pm25
    FROM cams_air_quality_data
    WHERE predicted_pm2_5 IS NOT NULL
    ORDER BY city, timestamp DESC
),
stream_latest AS (
    SELECT DISTINCT ON (city)
        city,
        timestamp AS stream_time,
        pm25 AS actual_pm25
    FROM air_quality_stream
    WHERE pm25 IS NOT NULL
    ORDER BY city, timestamp DESC
)
INSERT INTO forecast_comparison_results (
    city,
    batch_time,
    stream_time,
    predicted_pm25,
    actual_pm25,
    error_value,
    absolute_error,
    source_note
)
SELECT
    b.city,
    b.batch_time,
    s.stream_time,
    b.predicted_pm25,
    s.actual_pm25,
    s.actual_pm25 - b.predicted_pm25 AS error_value,
    ABS(s.actual_pm25 - b.predicted_pm25) AS absolute_error,
    'Latest city-level batch prediction compared with latest stream actual. Time periods may differ.'
FROM batch_latest b
JOIN stream_latest s
ON b.city = s.city;
"""

with engine.begin() as conn:
    conn.execute(text(QUERY))

print("forecast_comparison_results updated.")