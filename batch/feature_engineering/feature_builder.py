from pathlib import Path
import pandas as pd
import logging

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("CAMS feature engineering started")

try:
    INPUT_FILE = Path("data/processed/cams_clean.csv")
    OUTPUT_FILE = Path("data/processed/cams_feature_dataset.csv")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.info(f"Loading cleaned CAMS data from {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    logging.info(f"Input data shape: {df.shape}")

    df["time"] = pd.to_datetime(df["time"])

    df = df.sort_values(["city", "time"])

    df["hour"] = df["time"].dt.hour
    df["day"] = df["time"].dt.day
    df["month"] = df["time"].dt.month
    df["day_of_week"] = df["time"].dt.dayofweek

    logging.info("Time-based features created")

    df["pm2_5_rolling_3h"] = (
        df.groupby("city")["cams_pm2_5"]
        .transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    )

    df["pm10_rolling_3h"] = (
        df.groupby("city")["cams_pm10"]
        .transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    )

    df["pm2_5_lag_1"] = (
        df.groupby("city")["cams_pm2_5"]
        .shift(1)
    )

    df["pm10_lag_1"] = (
        df.groupby("city")["cams_pm10"]
        .shift(1)
    )

    logging.info("Rolling and lag features created")

    before_drop = df.shape[0]

    df = df.dropna()

    after_drop = df.shape[0]

    logging.info(
        f"Missing values dropped: {before_drop - after_drop} rows removed"
    )

    df.to_csv(OUTPUT_FILE, index=False)

    logging.info(
        f"CAMS feature engineering completed with shape {df.shape}"
    )

    logging.info(
        f"Feature dataset saved to {OUTPUT_FILE}"
    )

    print("CAMS feature engineering completed.")
    print(df.shape)

except Exception as e:
    logging.error("CAMS feature engineering failed")
    logging.exception(e)
    raise