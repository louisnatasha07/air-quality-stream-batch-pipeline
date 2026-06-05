from pathlib import Path
import pandas as pd
import joblib
import logging
import json

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# Path Config
LOG_DIR = Path("logs")
MODEL_DIR = Path("models")

LOG_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = Path("data/processed/cams_feature_dataset.csv")
MODEL_FILE = MODEL_DIR / "trained_model.pkl"
METRICS_FILE = MODEL_DIR / "model_metrics.json"

# Logging Config
logging.basicConfig(
    filename=LOG_DIR / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Model Config
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

TIME_COLUMN_CANDIDATES = ["time", "timestamp", "date"]


def get_time_column(df: pd.DataFrame) -> str:
    """
    Mencari kolom waktu yang tersedia di dataset.
    Prioritas: time -> timestamp -> date
    """
    for col in TIME_COLUMN_CANDIDATES:
        if col in df.columns:
            return col

    raise ValueError(
        f"Tidak ada kolom waktu. Dataset harus punya salah satu: {TIME_COLUMN_CANDIDATES}"
    )


def validate_columns(df: pd.DataFrame, time_col: str):
    """
    Validasi apakah semua kolom yang dibutuhkan tersedia.
    """
    required_columns = FEATURES + [TARGET, time_col]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Kolom berikut tidak ditemukan di dataset: {missing_columns}"
        )


def time_based_split(df: pd.DataFrame, time_col: str, test_size: float = 0.2):
    """
    Split data berdasarkan waktu.

    Kalau ada kolom city:
    - split dilakukan per kota
    - 80% data awal tiap kota untuk training
    - 20% data akhir tiap kota untuk testing

    Kalau tidak ada kolom city:
    - split dilakukan secara global berdasarkan waktu
    """

    df = df.sort_values(time_col).copy()

    if "city" in df.columns:
        logging.info("Using city-level time-based split")

        df = df.sort_values(["city", time_col]).copy()

        df["row_number"] = df.groupby("city").cumcount()
        df["total_rows"] = df.groupby("city")["row_number"].transform("max") + 1

        train_df = df[
            df["row_number"] < df["total_rows"] * (1 - test_size)
        ].copy()

        test_df = df[
            df["row_number"] >= df["total_rows"] * (1 - test_size)
        ].copy()

        train_df = train_df.drop(columns=["row_number", "total_rows"])
        test_df = test_df.drop(columns=["row_number", "total_rows"])

    else:
        logging.info("Using global time-based split")

        split_index = int(len(df) * (1 - test_size))

        train_df = df.iloc[:split_index].copy()
        test_df = df.iloc[split_index:].copy()

    if train_df.empty:
        raise ValueError("Train data kosong setelah time-based split.")

    if test_df.empty:
        raise ValueError("Test data kosong setelah time-based split.")

    return train_df, test_df


def main():
    logging.info("Model training started")

    try:
        logging.info(f"Loading feature dataset from {INPUT_FILE}")

        if not INPUT_FILE.exists():
            raise FileNotFoundError(f"File tidak ditemukan: {INPUT_FILE}")

        df = pd.read_csv(INPUT_FILE)

        logging.info(f"Dataset loaded with shape {df.shape}")

        time_col = get_time_column(df)

        logging.info(f"Using time column: {time_col}")

        validate_columns(df, time_col)

        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

        before_drop = len(df)

        drop_columns = FEATURES + [TARGET, time_col]

        if "city" in df.columns:
            drop_columns.append("city")

        df = df.dropna(subset=drop_columns).copy()

        after_drop = len(df)

        logging.info(
            f"Rows before dropna: {before_drop}, after dropna: {after_drop}"
        )

        if df.empty:
            raise ValueError("Dataset kosong setelah dropna.")

        train_df, test_df = time_based_split(
            df=df,
            time_col=time_col,
            test_size=0.2
        )

        X_train = train_df[FEATURES]
        y_train = train_df[TARGET]

        X_test = test_df[FEATURES]
        y_test = test_df[TARGET]

        logging.info(
            f"Train shape: {X_train.shape}, Test shape: {X_test.shape}"
        )

        logging.info(
            f"Train period: {train_df[time_col].min()} to {train_df[time_col].max()}"
        )

        logging.info(
            f"Test period: {test_df[time_col].min()} to {test_df[time_col].max()}"
        )

        model = RandomForestRegressor(
            n_estimators=150,
            random_state=42,
            n_jobs=-1
        )

        logging.info("RandomForest model training started")

        model.fit(X_train, y_train)

        logging.info("Model training completed")

        predictions = model.predict(X_test)

        mae = mean_absolute_error(y_test, predictions)
        mse = mean_squared_error(y_test, predictions)
        rmse = mse ** 0.5
        r2 = r2_score(y_test, predictions)

        metrics = {
            "mae": float(mae),
            "mse": float(mse),
            "rmse": float(rmse),
            "r2": float(r2),
            "train_rows": int(X_train.shape[0]),
            "test_rows": int(X_test.shape[0]),
            "train_start": str(train_df[time_col].min()),
            "train_end": str(train_df[time_col].max()),
            "test_start": str(test_df[time_col].min()),
            "test_end": str(test_df[time_col].max()),
            "split_strategy": "time_based_split_per_city" if "city" in df.columns else "time_based_split_global",
            "features": FEATURES,
            "target": TARGET,
            "time_column": time_col,
            "model": "RandomForestRegressor",
            "n_estimators": 150,
            "random_state": 42
        }

        with open(METRICS_FILE, "w") as f:
            json.dump(metrics, f, indent=4)

        logging.info(f"Model metrics saved to {METRICS_FILE}")

        logging.info(f"MAE: {mae}")
        logging.info(f"MSE: {mse}")
        logging.info(f"RMSE: {rmse}")
        logging.info(f"R2: {r2}")

        joblib.dump(model, MODEL_FILE)

        logging.info(f"Model saved to {MODEL_FILE}")

        print("Model Evaluation - Time Based Split")
        print("-----------------------------------")
        print("Train rows:", X_train.shape[0])
        print("Test rows:", X_test.shape[0])
        print("Train period:", train_df[time_col].min(), "to", train_df[time_col].max())
        print("Test period:", test_df[time_col].min(), "to", test_df[time_col].max())
        print("MAE:", mae)
        print("MSE:", mse)
        print("RMSE:", rmse)
        print("R2:", r2)
        print()
        print(f"Model saved to {MODEL_FILE}")
        print(f"Metrics saved to {METRICS_FILE}")
        print("Model training completed.")

    except Exception as e:
        logging.error("Model training failed")
        logging.exception(e)
        raise


if __name__ == "__main__":
    main()
