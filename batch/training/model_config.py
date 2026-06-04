from pathlib import Path

DATASET_FILE = Path("data/processed/cams_feature_dataset.csv")
MODEL_FILE = Path("models/trained_model.pkl")
METRICS_FILE = Path("models/model_metrics.json")

FEATURES = [
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

TARGET = "cams_pm2_5"
TIME_COL = "time"