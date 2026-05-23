from pathlib import Path
import sys
import logging

import pandas as pd
import joblib

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
        alert_message = (
            f"ALERT: {anomaly_count} PM2.5 anomalies detected "
            "in CAMS batch data"
        )

        print(alert_message)

        logging.warning(alert_message)

    logging.info("Writing detailed CAMS data to PostgreSQL")

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

    print("CAMS final dataset inserted into PostgreSQL.")
    print(df.shape)

except Exception as e:
    logging.error("Load to PostgreSQL pipeline failed")
    logging.exception(e)
    raise