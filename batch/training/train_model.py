import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

df = pd.read_csv(
    "data/processed/final_multi_city_air_quality.csv"
)

df = df.dropna()

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

X = df[features]

y = df["pm2_5"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = RandomForestRegressor(
    n_estimators=150,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)

mse = mean_squared_error(y_test, predictions)

rmse = mse ** 0.5

r2 = r2_score(y_test, predictions)

print("Model Evaluation")
print("MAE:", mae)
print("MSE:", mse)
print("RMSE:", rmse)
print("R2:", r2)

joblib.dump(
    model,
    "models/trained_model.pkl"
)

print("Model training completed.")