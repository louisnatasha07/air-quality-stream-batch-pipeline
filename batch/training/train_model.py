import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

df = pd.read_csv("data/processed/merged_air_quality.csv")
df = df.dropna()

features = [
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "ozone",
    "hour",
    "day",
    "cams_pm2_5",
    "cams_pm10"
]

X = df[features]
y = df["pm2_5"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

mse = mean_squared_error(y_test, predictions)
mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print("Model Evaluation")
print("MSE:", mse)
print("MAE:", mae)
print("R2:", r2)

joblib.dump(model, "models/trained_model.pkl")

print("Merged dataset model trained and saved.")