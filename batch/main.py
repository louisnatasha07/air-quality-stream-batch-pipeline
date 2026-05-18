import sys
from pathlib import Path

import pandas as pd
import joblib

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from database.db_connection import engine

df = pd.read_csv(
    "data/processed/final_multi_city_air_quality.csv"
)

features = [
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "ozone",
    "hour",
    "day",
    "month",
    "day_of_week",
    "pm2_5_rolling_3h",
    "cams_pm2_5",
    "cams_pm10"
]

model = joblib.load(
    "models/trained_model.pkl"
)

df = df.dropna()

df["predicted_pm2_5"] = model.predict(
    df[features]
)

df["anomaly_threshold"] = (
    df.groupby("city")["pm2_5"]
    .transform(
        lambda x: x.mean() + 2 * x.std()
    )
)

df["is_anomaly"] = (
    df["pm2_5"] > df["anomaly_threshold"]
)

df.to_sql(
    "multi_city_air_quality_data",
    engine,
    if_exists="replace",
    index=False
)

summary = df.groupby("city").agg(
    average_pm25=("pm2_5", "mean"),
    max_pm25=("pm2_5", "max"),
    avg_prediction=("predicted_pm2_5", "mean"),
    anomaly_count=("is_anomaly", "sum"),
    latitude=("latitude", "first"),
    longitude=("longitude", "first"),
).reset_index()

summary.to_sql(
    "city_air_quality_summary",
    engine,
    if_exists="replace",
    index=False
)

print("Final dataset inserted into PostgreSQL.")
print(df.shape)