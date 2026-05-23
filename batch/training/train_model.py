from pathlib import Path
import pandas as pd
import joblib
import logging

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Model training started")

try:

    INPUT_FILE = Path("data/processed/cams_feature_dataset.csv")
    MODEL_DIR = Path("models")
    MODEL_FILE = MODEL_DIR / "trained_model.pkl"

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    logging.info(
        f"Loading feature dataset from {INPUT_FILE}"
    )

    df = pd.read_csv(INPUT_FILE)

    logging.info(
        f"Dataset loaded with shape {df.shape}"
    )

    df = df.dropna()

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

    target = "cams_pm2_5"

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    logging.info(
        f"Train shape: {X_train.shape}, Test shape: {X_test.shape}"
    )

    model = RandomForestRegressor(
        n_estimators=150,
        random_state=42
    )

    logging.info("RandomForest model training started")

    model.fit(X_train, y_train)

    logging.info("Model training completed")

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = mse ** 0.5
    r2 = r2_score(y_test, predictions)

    logging.info(f"MAE: {mae}")
    logging.info(f"MSE: {mse}")
    logging.info(f"RMSE: {rmse}")
    logging.info(f"R2: {r2}")

    print("Model Evaluation")
    print("MAE:", mae)
    print("MSE:", mse)
    print("RMSE:", rmse)
    print("R2:", r2)

    joblib.dump(model, MODEL_FILE)

    logging.info(
        f"Model saved to {MODEL_FILE}"
    )

    print(f"Model saved to {MODEL_FILE}")
    print("Model training completed.")

except Exception as e:

    logging.error("Model training failed")

    logging.exception(e)

    raise