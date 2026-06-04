from datetime import timedelta
import numpy as np
import pandas as pd

from database.db_connection import engine

CITIES = {
    "Jakarta": (-6.2088, 106.8456, 42),
    "Kuala Lumpur": (3.1390, 101.6869, 30),
    "Singapore": (1.3521, 103.8198, 24),
    "Surakarta": (-7.5561, 110.8317, 28),
}

np.random.seed(42)

# STREAM DEMO DATA
now = pd.Timestamp.utcnow().floor("h").tz_localize(None)
stream_rows = []

for city, (lat, lon, base_pm25) in CITIES.items():
    for i in range(48):
        ts = now - timedelta(hours=47 - i)
        pm25 = max(1, base_pm25 + np.sin(i / 4) * 8 + np.random.normal(0, 3))
        pm10 = pm25 * 1.8
        aqi = min(300, max(1, pm25 * 2.2))

        stream_rows.append({
            "timestamp": ts,
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "pm25": pm25,
            "pm10": pm10,
            "carbon_monoxide": 500 + pm25 * 20,
            "nitrogen_dioxide": 10 + pm25 * 0.4,
            "sulphur_dioxide": 5 + pm25 * 0.1,
            "ozone": 20 + pm25 * 0.5,
            "aqi": aqi,
            "is_anomaly": pm25 > 50 or aqi > 100,
            "anomaly_reason": "Demo anomaly" if pm25 > 50 or aqi > 100 else "Normal",
            "created_at": pd.Timestamp.utcnow().tz_localize(None),
        })

stream_df = pd.DataFrame(stream_rows)
stream_df.to_sql("air_quality_stream", engine, if_exists="replace", index=False)

# BATCH DEMO DATA
batch_rows = []
dates = pd.date_range("2024-09-01", "2025-08-31", freq="D")

for city, (lat, lon, base_pm25) in CITIES.items():
    for i, ts in enumerate(dates):
        cams_pm25 = max(1, base_pm25 + np.sin(i / 20) * 6 + np.random.normal(0, 2))
        cams_pm10 = cams_pm25 * 1.7
        predicted = cams_pm25 + np.random.normal(0, 2.5)

        batch_rows.append({
            "city": city,
            "time": ts,
            "timestamp": ts,
            "cams_pm2_5": cams_pm25,
            "cams_pm10": cams_pm10,
            "hour": ts.hour,
            "day": ts.day,
            "month": ts.month,
            "day_of_week": ts.dayofweek,
            "pm2_5_rolling_3h": cams_pm25,
            "pm10_rolling_3h": cams_pm10,
            "pm2_5_lag_1": cams_pm25,
            "pm10_lag_1": cams_pm10,
            "predicted_pm2_5": predicted,
            "is_anomaly": cams_pm25 > base_pm25 + 10,
        })

batch_df = pd.DataFrame(batch_rows)
batch_df.to_sql("cams_air_quality_data", engine, if_exists="replace", index=False)

summary = batch_df.groupby("city").agg(
    average_pm25=("cams_pm2_5", "mean"),
    max_pm25=("cams_pm2_5", "max"),
    avg_prediction=("predicted_pm2_5", "mean"),
    anomaly_count=("is_anomaly", "sum"),
).reset_index()

summary.to_sql("city_air_quality_summary", engine, if_exists="replace", index=False)

print("Demo data inserted successfully.")
print("Stream rows:", len(stream_df))
print("Batch rows:", len(batch_df))