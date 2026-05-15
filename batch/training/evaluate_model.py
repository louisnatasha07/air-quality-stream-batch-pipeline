import pandas as pd
import joblib

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

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

model = joblib.load("models/trained_model.pkl")

predictions = model.predict(X)

mae = mean_absolute_error(y, predictions)
mse = mean_squared_error(y, predictions)
r2 = r2_score(y, predictions)

print("Model Evaluation")
print("MAE:", mae)
print("MSE:", mse)
print("RMSE:", mse ** 0.5)
print("R2 Score:", r2)