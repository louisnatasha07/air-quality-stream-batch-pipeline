from pathlib import Path
import sys
import logging

import pandas as pd
import joblib

from batch.utils.telegram_alert import send_telegram_message

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Load to PostgreSQL pipeline started")

try:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

    from database.db_connection import engine

    DATA_FILE = Path("data/processed/cams_feature_dataset.csv")
    MODEL_FILE = Path("models/trained_model.pkl")

    logging.info(f"Loading feature dataset from {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    
    TARGET_CITIES = {
        "Jakarta",
        "Surakarta",
        "Kuala Lumpur",
        "Singapore",
    }
    
    actual_cities = set(df["city"].unique())
    unexpected_cities = actual_cities - TARGET_CITIES
    
    if unexpected_cities:
        raise ValueError(
            f"Unexpected cities found in batch dataset: {sorted(unexpected_cities)}"
            )
        
    df = df[df["city"].isin(TARGET_CITIES)]

    logging.info(f"Dataset loaded with shape {df.shape}")

    logging.info(f"Loading trained model from {MODEL_FILE}")
    model = joblib.load(MODEL_FILE)

    before_drop = df.shape[0]
    df = df.dropna()
    after_drop = df.shape[0]

    logging.info(
        f"Missing values dropped before inference: {before_drop - after_drop}"
    )

    features = [
        "cams_pm10",
        "hour",
        "day",
        "month",
        "day_of_week",
        "pm2_5_rolling_3h",
        "pm10_rolling_3h",
        "pm2_5_lag_1",
        "pm10_lag_1",
    ]

    logging.info("Running PM2.5 prediction")
    df["predicted_pm2_5"] = model.predict(df[features])

    logging.info("Calculating anomaly threshold")
    df["anomaly_threshold"] = (
        df.groupby("city")["cams_pm2_5"]
        .transform(lambda x: x.mean() + 2 * x.std())
    )

    df["is_anomaly"] = df["cams_pm2_5"] > df["anomaly_threshold"]

    anomaly_count = int(df["is_anomaly"].sum())

    logging.info(f"Total anomalies detected: {anomaly_count}")
    
    if anomaly_count > 0:
        anomaly_by_city = (
            df[df["is_anomaly"]]
            .groupby("city")
            .size()
            .reset_index(name="anomaly_count")
            )
        
        anomaly_detail = "\n".join(
            f"- {row.city}: {row.anomaly_count} anomalies"
            for row in anomaly_by_city.itertuples()
            )
        
        alert_message = (
            "BATCH ALERT: PM2.5 anomalies detected\n"
            f"Total anomalies: {anomaly_count}\n"
            f"{anomaly_detail}"
            )
        
        print(alert_message)
        logging.warning(alert_message)
        send_telegram_message(alert_message)

    df.to_sql(
        "cams_air_quality_data",
        engine,
        if_exists="replace",
        index=False
    )

    summary = df.groupby("city").agg(
        average_pm25=("cams_pm2_5", "mean"),
        max_pm25=("cams_pm2_5", "max"),
        avg_prediction=("predicted_pm2_5", "mean"),
        anomaly_count=("is_anomaly", "sum"),
    ).reset_index()

    logging.info("Writing city summary data to PostgreSQL")

    summary.to_sql(
        "city_air_quality_summary",
        engine,
        if_exists="replace",
        index=False
    )

    logging.info(
        f"CAMS final dataset inserted into PostgreSQL with shape {df.shape}"
    )

    logging.info("Load to PostgreSQL pipeline completed")
    
    success_message = (
        "BATCH SUCCESS: CAMS batch pipeline completed\n"
        f"Rows inserted: {len(df)}\n"
        f"Cities: {', '.join(sorted(df['city'].unique()))}\n"
        f"Anomalies detected: {anomaly_count}"
        )
    
    send_telegram_message(success_message)

    print("CAMS final dataset inserted into PostgreSQL.")
    print(df.shape)

except Exception as e:
    logging.error("Load to PostgreSQL pipeline failed")
    logging.exception(e)

    send_telegram_message(
        f"BATCH FAILED: Load to PostgreSQL pipeline failed\nError: {str(e)}"
    )

    raise